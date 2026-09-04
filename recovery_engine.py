from dataclasses import dataclass

@dataclass
class RecoveryDecision:
    action: str
    confidence: float
    reason: str
    max_retries: int
    stop: bool

def decide_recovery(row) -> RecoveryDecision:
    reason = row.get("failure_reason", "")
    attempts = int(row.get("attempts", 0))
    status = row.get("status", "")

    if status == "SUCCESS":
        return RecoveryDecision("STOP", 1.0, "Payment is already successful.", 0, True)

    if reason == "ALREADY_RECOVERED":
        return RecoveryDecision("STOP", 0.99, "Payment appears to have been recovered already.", 0, True)

    if reason in {"NETWORK_ERROR", "TIMEOUT"} and attempts < 2:
        return RecoveryDecision(
            "RETRY", 0.94,
            "Temporary payment failure is potentially recoverable; automated retry is bounded.",
            2, False
        )

    if reason in {"PAYMENT_METHOD_DECLINED", "INSUFFICIENT_FUNDS"} and attempts < 2:
        return RecoveryDecision(
            "REMIND", 0.88,
            "Payment-method/funds issue is better handled with a reminder or payment-link flow.",
            1, False
        )

    if reason == "REPEATED_FAILURE" or attempts >= 3:
        return RecoveryDecision(
            "ESCALATE", 0.97,
            "Repeated failures exceed the safe automated retry threshold; human review required.",
            0, True
        )

    return RecoveryDecision(
        "ESCALATE", 0.70,
        "Case does not meet an approved automated recovery rule.",
        0, True
    )
