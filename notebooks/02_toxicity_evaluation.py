"""
Notebook script: 02_toxicity_evaluation.py
Evaluates and reports Precision, Recall, and F1 score for pretrained toxic-bert vs TF-IDF + LogisticRegression baseline.
"""

import pandas as pd
from pathlib import Path
import sys

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import RAW_DATA_DIR
from src.toxicity_classifier import evaluate_toxicity_models


def run_toxicity_evaluation():
    csv_path = RAW_DATA_DIR / "jigsaw_test_sample.csv"
    if not csv_path.exists():
        print("Error: jigsaw_test_sample.csv not found. Please run notebooks/01_dataset_exploration.py first.")
        return

    test_df = pd.read_csv(csv_path)
    print("=" * 65)
    print("TOXICITY MODEL EVALUATION (Pretrained toxic-bert vs TF-IDF Baseline)")
    print("=" * 65)

    results = evaluate_toxicity_models(test_df)

    print("\n--- RESULTS SUMMARY ---")
    df_results = pd.DataFrame(results).T
    print(df_results.to_string())
    print("=" * 65)


if __name__ == "__main__":
    run_toxicity_evaluation()
