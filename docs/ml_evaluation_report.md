# ResolveAI ML Risk Engine — Held-Out Test Evaluation Report

**Model Version**: `v1.0.0` (Logistic Regression / Scikit-Learn Pipeline)  
**Evaluation Date**: 2026-09-05  
**Dataset**: Synthetic Dispute Transaction Dataset ($N = 10,000$, Fraud Rate: $11.60\%$)  
**Data Partitioning**: 70% Train ($7,000$), 15% Validation ($1,500$), 15% Held-Out Test ($1,500$) — Strict Stratified Split  

---

## 🎯 Model Selection Summary

Two candidate classifiers were trained on the $7,000$ training partition and compared on the $1,500$ validation partition:

| Candidate Model | Val Precision | Val Recall | Val F1-Score | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline: Logistic Regression** | **$100.00\%$** | $86.29\%$ | **$92.64\%$** | **Winner Selected** |
| **Primary: RandomForestClassifier** | $98.70\%$ | $86.86\%$ | $92.40\%$ | Evaluated |

---

## 📈 Held-Out Test Set Performance (N = 1,500)

The selected **Logistic Regression Model** was evaluated **ONCE** on the held-out test dataset ($1,500$ samples).

| Metric | Result | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Precision** | **$96.45\%$** | $\ge 88.0\%$ | ✅ PASSED |
| **Recall** | **$93.68\%$** | $\ge 90.0\%$ | ✅ PASSED |
| **F1-Score** | **$95.04\%$** | $\ge 89.0\%$ | ✅ PASSED |
| **ROC-AUC** | **$0.9987$** | $\ge 0.950$ | ✅ PASSED |
| **False Positive Rate (FPR)** | **$0.45\%$** | $\le 3.0\%$ | ✅ PASSED |
| **False Negative Rate (FNR)** | **$6.32\%$** | $\le 7.0\%$ | ✅ PASSED |

---

## 🧩 Confusion Matrix & Financial Cost Matrix Analysis

### Confusion Matrix Breakdown (Held-out Test $N = 1,500$)
```text
                  Predicted Legitimate (0)     Predicted Fraud (1)
Actual Legitimate (0)        1,320 (TN)                  6 (FP)
Actual Fraud (1)                11 (FN)                163 (TP)
```

### Financial Risk Loss Calculation
* **False Positive Cost ($C_{FP}$)**: Merchant manual review cost per misclassified dispute = **₹200**
* **False Negative Cost ($C_{FN}$)**: Full lost transaction amount + chargeback penalty = **₹8,500**

$$\text{Total Expected Risk Loss} = (FP \times C_{FP}) + (FN \times C_{FN})$$

$$\text{Total Expected Risk Loss} = (6 \times ₹200) + (11 \times ₹8,500) = ₹1,200 + ₹93,500 = \mathbf{₹94,700.00}$$

> [!TIP]  
> **Cost Tradeoff Insight**:  
> Missed fraud cases ($FN$) account for $98.73\%$ of total financial risk exposure. The ML Risk Engine's $93.68\%$ recall minimizes missed chargebacks while maintaining an extremely low $0.45\%$ False Positive Rate ($6$ false alarms across $1,500$ disputes).

---

## 🧠 ML Engine vs AI Investigator Distinction

* **ML Risk Engine**: Computes pure numerical probability score $S \in [0.0, 1.0]$ deterministically. It does NOT generate text explanations or execute financial calls.
* **AI Investigator Agent**: Consumes the ML score along with multi-source tool evidence (customer history, delivery confirmation, transaction device hash) to construct an executive investigation summary and evidence matrix.

---

## ⚠️ Synthetic Data Limitations & Future Production Roadmap

1. **Synthetic Data Distributions**: The current dataset uses synthetic distribution generators (`dataset_generator.py`). Production deployment requires retraining on real merchant transaction logs.
2. **Feature Concept Drift**: Online shopping behavior evolves seasonally; production environments should implement daily feature drift monitoring.
3. **Imbalanced Sampling**: Production datasets typically exhibit $< 1\%$ chargeback rates; techniques such as SMOTE or focal loss reweighting will be applied in production models.
