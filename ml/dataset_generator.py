import os
import numpy as np
import pandas as pd

def generate_synthetic_dataset(num_samples: int = 10000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)

    # 1. Feature generation
    account_age_days = np.random.exponential(scale=180, size=num_samples).astype(int)
    account_age_days = np.clip(account_age_days, 1, 1500)

    previous_orders = (account_age_days * np.random.uniform(0.01, 0.2, size=num_samples)).astype(int)
    previous_orders = np.clip(previous_orders, 0, 150)

    previous_disputes = np.random.choice([0, 1, 2, 3, 4], size=num_samples, p=[0.75, 0.15, 0.06, 0.03, 0.01])
    refund_count_30d = np.random.choice([0, 1, 2, 3, 5], size=num_samples, p=[0.70, 0.18, 0.08, 0.03, 0.01])

    transaction_amount = np.random.lognormal(mean=7.5, sigma=0.8, size=num_samples)  # Mean ~ ₹2000-5000
    transaction_amount = np.clip(transaction_amount, 100.0, 50000.0).round(2)

    hist_avg = np.random.lognormal(mean=7.3, sigma=0.6, size=num_samples)
    amount_vs_historical_avg_ratio = (transaction_amount / (hist_avg + 1.0)).round(2)
    amount_vs_historical_avg_ratio = np.clip(amount_vs_historical_avg_ratio, 0.1, 15.0)

    carrier_delivery_gap_hours = np.random.normal(loc=48, scale=24, size=num_samples)
    carrier_delivery_gap_hours = np.clip(carrier_delivery_gap_hours, 2.0, 300.0).round(1)

    device_change_flag = np.random.choice([0, 1], size=num_samples, p=[0.82, 0.18])
    ip_country_mismatch = np.random.choice([0, 1], size=num_samples, p=[0.91, 0.09])
    order_velocity_24h = np.random.poisson(lam=1.5, size=num_samples) + 1

    delivery_confirmation_valid = np.random.choice([0, 1], size=num_samples, p=[0.20, 0.80])

    # 2. Ground truth probabilistic label generator (Log-odds formula)
    log_odds = (
        -1.5
        + 2.1 * device_change_flag
        + 2.4 * ip_country_mismatch
        + 0.45 * previous_disputes
        + 0.35 * refund_count_30d
        + 0.18 * np.log1p(amount_vs_historical_avg_ratio)
        + 0.12 * order_velocity_24h
        - 0.02 * np.sqrt(previous_orders)
        - 1.8 * delivery_confirmation_valid
    )

    probs = 1.0 / (1.0 + np.exp(-log_odds))
    is_fraudulent_dispute = (probs > 0.50).astype(int)

    df = pd.DataFrame({
        "transaction_amount": transaction_amount,
        "account_age_days": account_age_days,
        "previous_orders": previous_orders,
        "previous_disputes": previous_disputes,
        "refund_count_30d": refund_count_30d,
        "carrier_delivery_gap_hours": carrier_delivery_gap_hours,
        "device_change_flag": device_change_flag,
        "ip_country_mismatch": ip_country_mismatch,
        "order_velocity_24h": order_velocity_24h,
        "amount_vs_historical_avg_ratio": amount_vs_historical_avg_ratio,
        "delivery_confirmation_valid": delivery_confirmation_valid,
        "is_fraudulent_dispute": is_fraudulent_dispute,
        "fraud_probability_ground_truth": probs.round(4)
    })

    return df

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    df = generate_synthetic_dataset(num_samples=10000)
    output_path = os.path.join(output_dir, "synthetic_dispute_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic dispute records at {output_path}")
    print(f"Dispute Fraud Rate: {df['is_fraudulent_dispute'].mean():.2%}")
