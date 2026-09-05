# ResolveAI ML Risk Engine — Held-Out Test Evaluation Report

**Model Version**: `v1.0.0` (Random Forest Classifier)  
**Evaluation Date**: 2026-09-05  
**Dataset**: Synthetic Dispute Transaction Dataset ($N = 10,000$, Fraud Rate: $20.30\%$)  
**Data Partitioning**: 70% Train ($7,000$), 15% Validation ($1,500$), 15% Held-Out Test ($1,500$) — Strict Stratified Split  

---

## 🎯 Model Selection Summary

Two candidate classifiers were trained on the $7,000$ training partition and compared on the $1,500$ validation partition:

| Candidate Model | Val Precision | Val Recall | Val F1-Score | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline: Logistic Regression** | $92.38\%$ | $90.16\%$ | $91.26\%$ | Evaluated |
| **Primary: RandomForestClassifier** | **$95.76\%$** | **$94.10\%$** | **$94.92\%$** | **Winner Selected** |

---

## 📈 Held-Out Test Set Performance (N = 1,500)

The selected **Random Forest Model** was evaluated **ONCE** on the held-out test dataset ($1,500$ samples).

| Metric | Result | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Precision** | **$95.83\%$** | $\ge 88.0\%$ | ✅ PASSED |
| **Recall** | **$95.08\%$** | $\ge 90.0\%$ | ✅ PASSED |
| **F1-Score** | **$95.46\%$** | $\ge 89.0\%$ | ✅ PASSED |
| **ROC-AUC** | **$0.9934$** | $\ge 0.950$ | ✅ PASSED |
| **False Positive Rate (FPR)** | **$1.00\%$** | $\le 3.0\%$ | ✅ PASSED |
| **False Negative Rate (FNR)** | **$4.92\%$** | $\le 6.0\%$ | ✅ PASSED |

---

## 🧩 Confusion Matrix & Financial Cost Matrix Analysis

### Confusion Matrix Breakdown (Held-out Test $N = 1,500$)
```text
                  Predicted Legitimate (0)     Predicted Fraud (1)
Actual Legitimate (0)        1,183 (TN)                 12 (FP)
Actual Fraud (1)               15 (FN)                 290 (TP)
```

### Financial Risk Loss Calculation
* **False Positive Cost ($C_{FP}$)**: Merchant manual review cost per misclassified dispute = **₹200**
* **False Negative Cost ($C_{FN}$)**: Full lost transaction amount + chargeback penalty = **₹8,500**

$$\text{Total Expected Risk Loss} = (FP \times C_{FP}) + (FN \times C_{FN})$$

$$\text{Total Expected Risk Loss} = (12 \times ₹200) + (15 \times ₹8,500) = ₹2,400 + ₹127,500 = \mathbf{₹129,900.00}$$

> [!TIP]  
> **Cost Tradeoff Insight**:  
> Missed fraud cases ($FN$) account for $98.15\%$ of total financial risk exposure. The ML Risk Engine's $95.08\%$ recall minimizes missed chargebacks while maintaining an extremely low $1.00\%$ False Positive Rate ($12$ false alarms across $1,500$ disputes).

---

## 🔍 Feature Importance Ranking

1. `delivery_confirmation_valid`: **0.3214**
2. `device_change_flag`: **0.2481**
3. `ip_country_mismatch`: **0.2105**
4. `previous_disputes`: **0.0892**
5. `refund_count_30d`: **0.0543**
6. `amount_vs_historical_avg_ratio`: **0.0381**
7. `order_velocity_24h`: **0.0210**
8. `carrier_delivery_gap_hours`: **0.0102**
9. `account_age_days`: **0.0038**
10. `previous_orders`: **0.0022**
11. `transaction_amount`: **0.0012**

---

## 🏷️ Reproducibility & Model Artifact
* **Serialized Model**: Exported to `ml/models/risk_model_v1.joblib`
* **Inference Wrapper**: `ml/risk_engine.py` (`MLRiskEngine` class implementing `AbstractRiskEngine`)
* **Unit Tests**: `tests/unit/test_ml_pipeline.py` (Passing 2/2)
