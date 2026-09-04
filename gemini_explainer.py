import streamlit as st
from google import genai

# ==========================================================
# Gemini Client
# ==========================================================

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
except Exception:
    client = None


# ==========================================================
# Available Models
# ==========================================================

MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]


# ==========================================================
# Generate Explanation
# ==========================================================

def generate_explanation(row):

    if client is None:
        return "⚠️ Gemini client could not be initialized."

    failure_reason = row["failure_reason"]

    if str(failure_reason) == "nan":
        failure_reason = "None"

    prompt = f"""
You are RecoverAI.

Analyze this failed payment.

Payment ID: {row['payment_id']}
Amount: ₹{row['amount_inr']}
Failure Reason: {failure_reason}
Recommended Action: {row['action']}
Confidence: {round(float(row['confidence'])*100)}%
Recovery Result: {row['result']}

Explain:

• Why this action was selected.
• Business impact.
• Whether human review is needed.

Maximum 100 words.
Plain text only.
"""

    last_error = ""

    for model_name in MODELS:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if (
                response
                and hasattr(response, "text")
                and response.text
            ):
                return response.text.strip()

        except Exception as e:
            last_error = str(e)
            continue

    return (
        "⚠️ Gemini is temporarily unavailable.\n\n"
        "Google servers are busy.\n\n"
        f"Last Error:\n{last_error}"
    )