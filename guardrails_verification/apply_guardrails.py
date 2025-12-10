# 05_apply_guardrails.py
import pandas as pd

INPUT_CSV = "rubric_converted.csv"
OUTPUT_CSV = "all_reports_bands_guardrailed(ANA).csv"

def apply_guardrails(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply rule-based adjustments ("guardrails") to a copy of the band DataFrame.
    Returns a new DataFrame with adjusted scores and some flags.
    """
    adjusted = df.copy()

    # Example guardrail 1: If A3 < 3, mark a sequencing flag
    adjusted["flag_sequencing_issue"] = adjusted["A"] < 3

    # Example guardrail 2: If C3 < 2, cap C1<=2, C2<=3
    mask_c3_low = adjusted["E"] < 2
    adjusted.loc[mask_c3_low, "C"] = adjusted.loc[mask_c3_low, "C"].clip(upper=2)
    adjusted.loc[mask_c3_low, "D"] = adjusted.loc[mask_c3_low, "D"].clip(upper=3)
    adjusted["flag_retrieval_guardrail"] = mask_c3_low

    # Example guardrail 3: If D2 < 3, cap D3<=2
    mask_d2_low = adjusted["D"] < 3
    adjusted.loc[mask_d2_low, "E"] = adjusted.loc[mask_d2_low, "E"].clip(upper=2)
    adjusted["flag_scaffolding_guardrail"] = mask_d2_low

    # Example guardrail 4: If B3 < 3, cap B1<=3
    mask_b3_low = adjusted["C"] < 3
    adjusted.loc[mask_b3_low, "B"] = adjusted.loc[mask_b3_low, "B"].clip(upper=3)
    adjusted["flag_engagement_guardrail"] = mask_b3_low

    # Example guardrail 5: If E3 < 2, cap E1<=3
    mask_e3_very_low = adjusted["G"] < 2
    adjusted.loc[mask_e3_very_low, "E"] = adjusted.loc[mask_e3_very_low, "E"].clip(upper=3)
    adjusted["flag_load_guardrail"] = mask_e3_very_low

    # Recompute an overall mean AFTER guardrails
    criteria_cols = [c for c in df.columns if c.startswith(("A","B","C","D","E","F"))]
    adjusted["overall_mean_after_guardrails"] = adjusted[criteria_cols].mean(axis=1)

    return adjusted


def main():
    df = pd.read_csv(INPUT_CSV, index_col="model")
    print("Original bands:")
    print(df)

    adjusted = apply_guardrails(df)

    print("\nAdjusted bands + flags:")
    print(adjusted)

    adjusted.to_csv(OUTPUT_CSV)
    print(f"\nSaved adjusted scores with guardrails to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()