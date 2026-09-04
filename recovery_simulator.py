"""
RecoverAI - bounded test-mode recovery simulator.
Run:
    python recovery_simulator.py
"""
from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent
INPUT = BASE / "payments.csv"
AUDIT = BASE / "recovery_audit.csv"
METRICS = BASE / "recovery_metrics.csv"

rng = np.random.default_rng(20260904)
df = pd.read_csv(INPUT)

rows = []
for _, row in df.iterrows():
    amount = float(row["amount_inr"])
    status = row["status"]
    reason = row["failure_reason"]
    attempts = int(row["attempts"])

    if status == "SUCCESS":
        action, confidence, diagnosis, stop, stopping_rule = "STOP", 1.00, "Payment is already successful.", True, "Already successful"
        result, recovered = "NO_ACTION", 0.0
    elif reason == "ALREADY_RECOVERED":
        action, confidence, diagnosis, stop, stopping_rule = "STOP", 0.99, "Payment appears to have been recovered already.", True, "Already recovered"
        result, recovered = "NO_ACTION", 0.0
    elif reason in {"NETWORK_ERROR", "TIMEOUT"} and attempts < 2:
        action, confidence, diagnosis, stop, stopping_rule = "RETRY", 0.94, "Temporary gateway/network failure; bounded retry is appropriate.", False, "Retry within one-attempt limit"
        recovered = amount if rng.random() < 0.72 else 0.0
        result = "RECOVERED" if recovered else "FAILED_AFTER_RETRY"
    elif reason in {"PAYMENT_METHOD_DECLINED", "INSUFFICIENT_FUNDS"} and attempts < 2:
        action, confidence, diagnosis, stop, stopping_rule = "REMIND", 0.88, "Payment-method or funds issue; customer reminder/payment-link is safer than blind retry.", False, "Reminder sent; await customer action"
        probability = 0.45 if reason == "PAYMENT_METHOD_DECLINED" else 0.35
        recovered = amount if rng.random() < probability else 0.0
        result = "RECOVERED" if recovered else "CUSTOMER_ACTION_REQUIRED"
    elif reason == "REPEATED_FAILURE" or attempts >= 3:
        action, confidence, diagnosis, stop, stopping_rule = "ESCALATE", 0.97, "Repeated failures exceed automated retry threshold; human review required.", True, "Retry threshold exceeded"
        result, recovered = "ESCALATED", 0.0
    else:
        action, confidence, diagnosis, stop, stopping_rule = "ESCALATE", 0.70, "Case does not satisfy an approved automated recovery rule.", True, "No safe automated rule"
        result, recovered = "ESCALATED", 0.0

    rows.append({
        "payment_id": row["payment_id"],
        "amount_inr": amount,
        "original_status": status,
        "failure_reason": reason,
        "attempts": attempts,
        "diagnosis": diagnosis,
        "action": action,
        "confidence": confidence,
        "result": result,
        "recovered_amount_inr": recovered,
        "stopping_rule": stopping_rule,
    })

audit = pd.DataFrame(rows)
failed = audit[audit["original_status"] == "FAILED"]
at_risk = failed["amount_inr"].sum()
recovered = failed["recovered_amount_inr"].sum()

metrics = pd.DataFrame([{
    "total_payments": len(df),
    "failed_payments": len(failed),
    "at_risk_revenue_inr": at_risk,
    "recovered_payments": int((failed["result"] == "RECOVERED").sum()),
    "recovered_revenue_inr": recovered,
    "recovery_rate_percent": round(100 * recovered / at_risk, 2) if at_risk else 0,
    "escalated_cases": int((failed["result"] == "ESCALATED").sum()),
    "unresolved_cases": int(failed["result"].isin(["FAILED_AFTER_RETRY", "CUSTOMER_ACTION_REQUIRED", "ESCALATED"]).sum()),
}])

audit.to_csv(AUDIT, index=False)
metrics.to_csv(METRICS, index=False)
print(metrics.to_string(index=False))
