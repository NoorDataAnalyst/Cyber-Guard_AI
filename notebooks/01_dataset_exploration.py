"""
Notebook script: 01_dataset_exploration.py
Explores and computes summary statistics for the held-out Jigsaw toxic comment evaluation dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import RAW_DATA_DIR
from data.download_sample_data import generate_verified_jigsaw_sample


def explore_jigsaw_dataset():
    """Load Jigsaw dataset sample and display label distributions and text length statistics."""
    csv_path = RAW_DATA_DIR / "jigsaw_test_sample.csv"
    if not csv_path.exists():
        csv_path = generate_verified_jigsaw_sample()

    df = pd.read_csv(csv_path)
    print("=" * 60)
    print("JIGSAW TOXIC COMMENT DATASET EXPLORATION")
    print("=" * 60)
    print(f"Total Rows: {len(df)}")
    print("\nColumns:", list(df.columns))

    label_cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
    print("\n--- Label Distribution ---")
    for col in label_cols:
        count = df[col].sum()
        pct = (count / len(df)) * 100
        print(f"  {col:<15}: {count:3d} ({pct:5.1f}%)")

    # Clean vs Toxic split
    df["is_any_toxic"] = (df[label_cols].sum(axis=1) > 0).astype(int)
    clean_count = (df["is_any_toxic"] == 0).sum()
    toxic_count = (df["is_any_toxic"] == 1).sum()
    print(f"\nClean Comments: {clean_count} ({clean_count/len(df)*100:.1f}%)")
    print(f"Toxic Comments: {toxic_count} ({toxic_count/len(df)*100:.1f}%)")

    # Character and Word Length Stats
    df["char_length"] = df["comment_text"].apply(len)
    df["word_count"] = df["comment_text"].apply(lambda x: len(x.split()))

    print("\n--- Text Length Summary ---")
    print(f"Mean Word Count   : {df['word_count'].mean():.2f}")
    print(f"Max Word Count    : {df['word_count'].max()}")
    print(f"Min Word Count    : {df['word_count'].min()}")
    print("=" * 60)


if __name__ == "__main__":
    explore_jigsaw_dataset()
