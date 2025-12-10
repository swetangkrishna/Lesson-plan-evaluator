# 01_load_reports.py
import os
import glob
import json
import pandas as pd

REPORTS_DIR = "../reports_json"
OUTPUT_CSV = "all_reports_bands.csv"

def load_reports_to_df(reports_dir: str) -> pd.DataFrame:
    """
    Load all JSON report files and return a DataFrame:
    rows = models, columns = criteria (A1..F2), values = band scores.
    """
    rows = []

    json_paths = glob.glob(os.path.join(reports_dir, "*.json"))
    if not json_paths:
        raise FileNotFoundError(f"No JSON files found in {reports_dir}")

    for path in json_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        model_name = os.path.splitext(os.path.basename(path))[0]
        criteria = data.get("criteria", {})

        row = {"model": model_name}
        for crit_name, crit_obj in criteria.items():
            row[crit_name] = crit_obj.get("band", None)

        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("model").sort_index(axis=1)
    return df


def main():
    df = load_reports_to_df(REPORTS_DIR)
    print("Loaded data:")
    print(df)
    df.to_csv(OUTPUT_CSV)
    print(f"\nSaved band matrix to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()