# 03_threshold_analysis.py
import pandas as pd

INPUT_CSV = "rubric_converted.csv"

def conditional_summary(df: pd.DataFrame, focus_criterion: str, threshold: float):
    """
    Compare mean scores of other criteria when focus_criterion < threshold
    vs. >= threshold.
    """
    if focus_criterion not in df.columns:
        raise ValueError(f"{focus_criterion} not in columns: {df.columns.tolist()}")

    low_mask = df[focus_criterion] < threshold
    high_mask = ~low_mask

    print(f"\n=== Threshold analysis for {focus_criterion} at {threshold} ===")
    print(f"Rows with {focus_criterion} < {threshold}: {low_mask.sum()}")
    print(f"Rows with {focus_criterion} >= {threshold}: {high_mask.sum()}")

    low_mean = df[low_mask].mean(numeric_only=True)
    high_mean = df[high_mask].mean(numeric_only=True)

    summary = pd.DataFrame({
        f"{focus_criterion} < {threshold}": low_mean,
        f"{focus_criterion} >= {threshold}": high_mean
    })

    print("\nMean bands of other criteria by group:")
    print(summary.round(2))

    return summary


def main():
    df = pd.read_csv(INPUT_CSV, index_col="model")
    # Example: investigate C3 as a spacing/robustness criterion
    _ = conditional_summary(df, focus_criterion="C", threshold=2)
    # You can add more calls, e.g.:
    _ = conditional_summary(df, focus_criterion="A", threshold=3)
    _ = conditional_summary(df, focus_criterion="F", threshold=3)


if __name__ == "__main__":
    main()