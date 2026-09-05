import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    confusion_matrix, roc_auc_score
)
from ml.dataset_generator import generate_synthetic_dataset

FEATURE_COLUMNS = [
    "transaction_amount",
    "account_age_days",
    "previous_orders",
    "previous_disputes",
    "refund_count_30d",
    "carrier_delivery_gap_hours",
    "device_change_flag",
    "ip_country_mismatch",
    "order_velocity_24h",
    "amount_vs_historical_avg_ratio",
    "delivery_confirmation_valid"
]

TARGET_COLUMN = "is_fraudulent_dispute"

# Cost constants
COST_FP = 200.0   # Merchant manual review cost for false positive (₹200)
COST_FN = 8500.0  # Lost transaction + chargeback fee for false negative (₹8,500)

def train_and_evaluate():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_dispute_data.csv")
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        df = generate_synthetic_dataset()

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Step 1: 70/15/15 Train / Val / Test Split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    print(f"Data split: Train={len(X_train)}, Val={len(X_val)}, Held-out Test={len(X_test)}")

    # Step 2: Baseline Model (Logistic Regression)
    baseline_model = LogisticRegression(max_iter=1000, random_state=42)
    baseline_model.fit(X_train, y_train)

    val_preds_base = baseline_model.predict(X_val)
    val_prec_base = precision_score(y_val, val_preds_base)
    val_rec_base = recall_score(y_val, val_preds_base)
    val_f1_base = f1_score(y_val, val_preds_base)

    print("\n--- Baseline Model (Logistic Regression) Validation Performance ---")
    print(f"Precision: {val_prec_base:.4f} | Recall: {val_rec_base:.4f} | F1: {val_f1_base:.4f}")

    # Step 3: Primary Model (Random Forest Classifier)
    primary_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        random_state=42
    )
    primary_model.fit(X_train, y_train)

    val_preds_prim = primary_model.predict(X_val)
    val_prec_prim = precision_score(y_val, val_preds_prim)
    val_rec_prim = recall_score(y_val, val_preds_prim)
    val_f1_prim = f1_score(y_val, val_preds_prim)

    print("\n--- Primary Model (Random Forest) Validation Performance ---")
    print(f"Precision: {val_prec_prim:.4f} | Recall: {val_rec_prim:.4f} | F1: {val_f1_prim:.4f}")

    # Model selection based on Validation F1 Score
    if val_f1_prim >= val_f1_base:
        selected_model = primary_model
        selected_model_name = "RandomForestClassifier"
    else:
        selected_model = baseline_model
        selected_model_name = "LogisticRegression"

    print(f"\nWinner Selected via Validation F1: {selected_model_name}")

    # Step 4: ONCE-ONLY Evaluation on Held-Out Test Set
    test_preds = selected_model.predict(X_test)
    test_probs = selected_model.predict_proba(X_test)[:, 1]

    prec = precision_score(y_test, test_preds)
    rec = recall_score(y_test, test_preds)
    f1 = f1_score(y_test, test_preds)
    auc = roc_auc_score(y_test, test_probs)

    tn, fp, fn, tp = confusion_matrix(y_test, test_preds).ravel()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    total_cost = (fp * COST_FP) + (fn * COST_FN)

    if hasattr(selected_model, "feature_importances_"):
        importances = selected_model.feature_importances_.round(4).tolist()
    else:
        importances = np.abs(selected_model.coef_[0]).round(4).tolist()

    metrics_report = {
        "model_name": selected_model_name,
        "test_samples": len(X_test),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
        "confusion_matrix": {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp)
        },
        "false_positive_rate": round(float(fpr), 4),
        "false_negative_rate": round(float(fnr), 4),
        "financial_impact": {
            "fp_cost_inr": float(fp * COST_FP),
            "fn_cost_inr": float(fn * COST_FN),
            "total_risk_loss_inr": float(total_cost)
        },
        "feature_importances": dict(zip(FEATURE_COLUMNS, importances))
    }

    print("\n================ HELD-OUT TEST EVALUATION ================")
    print(f"Model: {selected_model_name}")
    print(f"Precision : {prec:.4%}")
    print(f"Recall    : {rec:.4%}")
    print(f"F1-Score  : {f1:.4%}")
    print(f"ROC-AUC   : {auc:.4f}")
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"False Positive Rate: {fpr:.2%}")
    print(f"False Negative Rate: {fnr:.2%}")
    print(f"Estimated Risk Cost: INR {total_cost:,.2f} (FP Cost: INR {fp*COST_FP:,.2f}, FN Cost: INR {fn*COST_FN:,.2f})")

    # Step 5: Save Model
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "risk_model_v1.joblib")
    
    saved_payload = {
        "model": selected_model,
        "feature_columns": FEATURE_COLUMNS,
        "model_version": "v1.0.0",
        "metrics": metrics_report
    }
    joblib.dump(saved_payload, model_path)
    print(f"\nModel pipeline successfully exported to {model_path}")

    return metrics_report

if __name__ == "__main__":
    train_and_evaluate()
