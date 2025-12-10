# 04_decision_tree_rules.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

INPUT_CSV = "rubric_converted.csv"

def main():
    df = pd.read_csv(INPUT_CSV, index_col="model")

    # Simple overall score = mean band across all criteria
    df["overall_mean"] = df.mean(axis=1, numeric_only=True)

    # Binary label: 1 = good (>= 2.5), 0 = needs review (< 2.5)
    df["label_good"] = (df["overall_mean"] >= 2.5).astype(int)

    feature_cols = [c for c in df.columns if c.startswith(("A", "B", "C", "D", "E", "F", "G"))]
    X = df[feature_cols]
    y = df["label_good"]

    clf = DecisionTreeClassifier(
        max_depth=3,  # keep the tree small / interpretable
        min_samples_split=2,
        random_state=42
    )
    clf.fit(X, y)

    # Show the decision rules
    tree_rules = export_text(clf, feature_names=list(X.columns))
    print("=== Decision tree rules (candidate guardrails) ===")
    print(tree_rules)

    # Optional: inspect feature importances
    importances = pd.Series(clf.feature_importances_, index=X.columns)
    print("\nFeature importances:")
    print(importances[importances > 0].sort_values(ascending=False))


if __name__ == "__main__":
    main()