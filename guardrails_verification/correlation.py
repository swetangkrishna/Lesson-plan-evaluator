# 02_correlations.py
import pandas as pd

INPUT_CSV = "rubric_converted.csv"
OUTPUT_CSV = "criteria_correlations(ANA).csv"

def main():
    df = pd.read_csv(INPUT_CSV, index_col="model")
    print("Loaded band data:")
    print(df)

    # Pearson correlation between criteria
    corr = df.corr(method="pearson")
    print("\nCorrelation matrix:")
    print(corr.round(3))

    corr.to_csv(OUTPUT_CSV)
    print(f"\nSaved correlation matrix to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()