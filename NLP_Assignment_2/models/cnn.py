import torch
import torch.nn as nn




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
        # x: (B, T)
        emb = self.emb_dropout(self.embedding(x))  # (B, T, E)
        emb_t = emb.transpose(1, 2)  # (B, E, T) for Conv1d
        pooled = []
        for conv in self.convs:
            z = torch.relu(conv(emb_t))  # (B, F, T-k+1)
            p = torch.max(z, dim=2).values  # (B, F)
            pooled.append(p)
        rep = torch.cat(pooled, dim=1)  # (B, F * |K|)
        rep = self.rep_dropout(rep)
        return self.fc(rep)
