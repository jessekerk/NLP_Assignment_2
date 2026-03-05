import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from collections import Counter
import matplotlib.pyplot as plt
from pandas import DataFrame
import time
import random
import numpy as np
import re

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def download_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_120k_samples = pd.read_json(
        "hf://datasets/sh0416/ag_news/train.jsonl", lines=True
    )
    test_7k_samples = pd.read_json(
        "hf://datasets/sh0416/ag_news/test.jsonl", lines=True
    )
    return (train_120k_samples, test_7k_samples)


def split_training_data(
    data: pd.DataFrame, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df, temp_df = train_test_split(
        data, test_size=0.2, random_state=seed, shuffle=True
    )
    dev_df, test_df = train_test_split(
        temp_df, test_size=0.5, random_state=seed, shuffle=True
    )
    return (train_df, dev_df, test_df)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["text"] = df["title"] + " " + df["description"]
    df["label"] = df["label"] - 1
    return df[["text", "label"]]


def tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.split()


PAD = "<PAD>"
UNK = "<UNK>"


def build_vocab(texts, min_freq=2):
    counter = Counter()
    for text in texts:
        counter.update(tokenize(text))
    vocab = {PAD: 0, UNK: 1}
    for word, freq in counter.items():
        if freq >= min_freq:
            vocab[word] = len(vocab)
    return vocab


def numericalize(tokens, vocab):
    return [vocab.get(t, vocab[UNK]) for t in tokens]


def encode(text, vocab, max_len):
    ids = numericalize(tokenize(text), vocab)
    if len(ids) < max_len:
        ids += [vocab[PAD]] * (max_len - len(ids))
    else:
        ids = ids[:max_len]
    return ids


class TextDataset(Dataset):
    def __init__(self, data, vocab, max_len=200):
        self.data = data
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data[idx]
        x = encode(row["text"], self.vocab, self.max_len)
        y = row["label"]
        return torch.tensor(x), y


def collate(batch):
    xs, ys = zip(*batch)
    xs = torch.stack(xs)
    ys = torch.tensor(ys)
    lengths = (xs != 0).sum(dim=1)
    return xs, lengths, ys


class CNNTextClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        num_filters: int = 64,
        kernel_sizes: tuple = (3, 4, 5),
        dropout: float = 0.3,
        pad_idx: int = 0,
        num_classes: int = 2,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.emb_dropout = nn.Dropout(dropout)
        self.convs = nn.ModuleList(
            [
                nn.Conv1d(
                    in_channels=embed_dim, out_channels=num_filters, kernel_size=k
                )
                for k in kernel_sizes
            ]
        )
        self.rep_dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_filters * len(kernel_sizes), num_classes)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        emb = self.emb_dropout(self.embedding(x))
        emb_t = emb.transpose(1, 2)
        pooled = []
        for conv in self.convs:
            z = torch.relu(conv(emb_t))
            p = torch.max(z, dim=2).values
            pooled.append(p)
        rep = torch.cat(pooled, dim=1)
        rep = self.rep_dropout(rep)
        return self.fc(rep)


class LSTMClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
        pad_idx: int = 0,
        num_classes: int = 2,
        bidirectional: bool = False,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.emb_dropout = nn.Dropout(dropout)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional,
        )
        rep_dim = hidden_dim * (2 if bidirectional else 1)
        self.rep_dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(rep_dim, num_classes)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        emb = self.emb_dropout(self.embedding(x))
        packed = nn.utils.rnn.pack_padded_sequence(
            emb, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, (h_n, _) = self.lstm(packed)
        h_last = h_n[-1]
        rep = self.rep_dropout(h_last)
        return self.fc(rep)


def evaluate(model, loader):
    model.eval()
    preds = []
    gold = []
    with torch.no_grad():
        for x, lengths, y in loader:
            x = x.to(device)
            lengths = lengths.to(device)
            logits = model(x, lengths)
            pred = torch.argmax(logits, dim=1).cpu().numpy()
            preds.extend(pred)
            gold.extend(y.numpy())
    acc = accuracy_score(gold, preds)
    f1 = f1_score(gold, preds, average="macro")
    return {"acc": acc, "f1": f1}


def fit(model, train_loader, val_loader, lr, max_epochs, patience, clip_grad_norm):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    best_f1 = 0
    wait = 0
    hist = []
    for epoch in range(1, max_epochs + 1):
        model.train()
        total_loss = 0
        for x, lengths, y in train_loader:
            x = x.to(device)
            lengths = lengths.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            logits = model(x, lengths)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad_norm)
            optimizer.step()
            total_loss += loss.item()
        val = evaluate(model, val_loader)
        hist.append(
            {
                "epoch": epoch,
                "val_loss": total_loss / len(train_loader),
                "val_f1": val["f1"],
            }
        )
        if val["f1"] > best_f1:
            best_f1 = val["f1"]
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break
    return hist


train_raw, _ = download_data()
train_df, dev_df, test_df = split_training_data(train_raw)
train_df = preprocess(train_df)
dev_df = preprocess(dev_df)
test_df = preprocess(test_df)
train_data = train_df.to_dict("records")
dev_data = dev_df.to_dict("records")
test_data = test_df.to_dict("records")
raw = {"test": test_data}

vocab = build_vocab(train_df["text"])
PAD_IDX = vocab[PAD]
MAX_LEN = 200
vocab_size = len(vocab)

train_ds = TextDataset(train_data, vocab, MAX_LEN)
dev_ds = TextDataset(dev_data, vocab, MAX_LEN)
test_ds = TextDataset(test_data, vocab, MAX_LEN)

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, collate_fn=collate)
val_loader = DataLoader(dev_ds, batch_size=64, collate_fn=collate)
test_loader = DataLoader(test_ds, batch_size=64, collate_fn=collate)

set_seed(13)

MAX_EPOCHS = 12
PATIENCE = 3
LR = 1e-3
CLIP = 1.0


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_and_time(name: str, model: nn.Module):
    t0 = time.perf_counter()
    hist = fit(
        model,
        train_loader,
        val_loader,
        lr=LR,
        max_epochs=MAX_EPOCHS,
        patience=PATIENCE,
        clip_grad_norm=CLIP,
    )
    total_time = time.perf_counter() - t0
    val = evaluate(model, val_loader)
    test = evaluate(model, test_loader)
    return {
        "name": name,
        "hist": hist,
        "val": val,
        "test": test,
        "time_s_total": total_time,
    }


lstm = LSTMClassifier(
    vocab_size=vocab_size,
    embed_dim=64,
    hidden_dim=64,
    num_layers=2,
    dropout=0.3,
    pad_idx=PAD_IDX,
    num_classes=4,
).to(device)
cnn = CNNTextClassifier(
    vocab_size=vocab_size,
    embed_dim=64,
    num_filters=64,
    kernel_sizes=(3, 4, 5),
    dropout=0.3,
    pad_idx=PAD_IDX,
    num_classes=4,
).to(device)

print("Number of trainable parameters:")
print("LSTM:", count_parameters(lstm))
print("CNN:", count_parameters(cnn))

print("Training LSTM...")
res_lstm = train_and_time("LSTM", lstm)

print("Training CNN...")
res_cnn = train_and_time("CNN", cnn)

rows = []
for res in [res_lstm, res_cnn]:
    rows.append(
        [
            res["name"],
            res["val"]["acc"],
            res["val"]["f1"],
            res["test"]["acc"],
            res["test"]["f1"],
            res["time_s_total"],
        ]
    )

df_compare = (
    DataFrame(
        rows,
        columns=[
            "model",
            "val_acc",
            "val_macro_f1",
            "test_acc",
            "test_macro_f1",
            "train_time_s",
        ],
    )
    .sort_values(by=["val_macro_f1", "val_acc"], ascending=False)
    .reset_index(drop=True)
)

print(df_compare)


def plot_learning_curves(results, key, title, ylabel):
    plt.figure()
    for res in results:
        hist = res["hist"]
        epochs = [h["epoch"] for h in hist]
        vals = [h[key] for h in hist]
        plt.plot(epochs, vals, label=res["name"])
    plt.xlabel("epoch")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.show()


plot_learning_curves([res_lstm, res_cnn], "val_loss", "Validation loss", "loss")
plot_learning_curves([res_lstm, res_cnn], "val_f1", "Validation macro F1", "macro F1")

LABELS = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}


def get_misclassified_examples(model: nn.Module, raw_split, max_items: int = 8):
    model.eval()
    errs = []
    for ex in raw_split:
        tokens = tokenize(ex["text"])
        ids = numericalize(tokens, vocab)[:MAX_LEN]
        x = torch.tensor(ids, dtype=torch.long).unsqueeze(0).to(device)
        lengths = torch.tensor([len(ids)], dtype=torch.long).to(device)
        y = int(ex["label"])
        with torch.no_grad():
            logits = model(x, lengths)
            pred = int(logits.argmax(dim=1).item())
        if pred != y:
            snippet = ex["text"].replace("\n", " ")
            snippet = snippet[:250] + ("..." if len(snippet) > 250 else "")
            errs.append((y, pred, snippet))
        if len(errs) >= max_items:
            break
    return errs


errs_lstm = get_misclassified_examples(lstm, raw["test"], 10)
errs_cnn = get_misclassified_examples(cnn, raw["test"], 10)


def show_errors(name: str, errs):
    print(name)
    for i, (y, p, snip) in enumerate(errs):
        print()
        print(f"error {i + 1}")
        print("true:", LABELS[y], "pred:", LABELS[p])
        print("text:", snip)


show_errors("LSTM errors", errs_lstm[:8])
print("\n" + "=" * 80 + "\n")
show_errors("CNN errors", errs_cnn[:8])
