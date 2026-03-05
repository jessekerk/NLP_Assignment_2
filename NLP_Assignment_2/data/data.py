import pandas as pd
from sklearn.model_selection import train_test_split


def download_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_120k_samples: pd.DataFrame = pd.read_json(
        "hf://datasets/sh0416/ag_news/train.jsonl", lines=True
    )

    test_7k_samples: pd.DataFrame = pd.read_json(
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
