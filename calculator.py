"""
Advanced Token & Cost Estimator for Claude and Gemini (2025 API rates)

Estimates cost based on both input (prompt) AND expected output.
Assumes output token count is estimated as a ratio of prompt tokens.
"""

import json
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, message_dialog

# --- Pricing (USD per 1M tokens) ---
PRICING = {
    "claude": {"input_per_m": 3.00, "output_per_m": 15.00},
    "gemini": {"input_per_m": 1.25, "output_per_m": 10.00},
}

# USD → EUR conversion rate — adjust as needed
USD_TO_EUR = 0.92

def count_tokens(text: str) -> int:
    """Very rough token estimation: assume ~1 token per 0.75 words."""
    words = len(text.split())
    tokens = int(words / 0.75)
    return tokens

def estimate_cost(tokens: int, model: str, output_tokens: int = 0):
    """Estimate cost in EUR, for input + output tokens."""
    pricing = PRICING.get(model)
    if pricing is None:
        return 0.0
    cost_usd = (tokens / 1_000_000) * pricing["input_per_m"]
    cost_usd += (output_tokens / 1_000_000) * pricing["output_per_m"]
    cost_eur = cost_usd * USD_TO_EUR
    return round(cost_eur, 6)

def save_last(data: dict):
    with open("last_estimate.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    models = checkboxlist_dialog(
        title="Select Model(s)",
        text="Which model(s) to estimate for?",
        values=[("claude", "Claude"), ("gemini", "Gemini")]
    ).run()
    if not models:
        message_dialog(title="Error", text="No model selected — exiting.").run()
        return

    prompt_text = input_dialog(
        title="Prompt Text",
        text="Enter your prompt (multi-line allowed):"
    ).run()
    if not prompt_text or not prompt_text.strip():
        message_dialog(title="Error", text="Prompt is empty — exiting.").run()
        return

    # Ask user for expected output size (in tokens) or ratio
    resp = input_dialog(
        title="Expected Response Size",
        text=(
            "Enter expected OUTPUT token count (integer),\n"
            "or leave blank to assume output = prompt tokens."
        )
    ).run()

    try:
        if resp and resp.strip():
            output_tokens = int(resp.strip())
        else:
            # default: assume output tokens ≈ prompt tokens
            output_tokens = None
    except ValueError:
        output_tokens = None

    results = {}
    for m in models:
        input_tokens = count_tokens(prompt_text)
        out_tokens = output_tokens if output_tokens is not None else input_tokens
        cost = estimate_cost(input_tokens, m, out_tokens)
        results[m] = {
            "input_tokens": input_tokens,
            "output_tokens": out_tokens,
            "estimated_cost_eur": cost
        }

    display = ""
    for m, r in results.items():
        display += (
            f"{m.title()}:\n"
            f"  Input Tokens: {r['input_tokens']}\n"
            f"  Output Tokens: {r['output_tokens']}\n"
            f"  Estimated Cost (EUR): €{r['estimated_cost_eur']}\n\n"
        )

    message_dialog(title="Estimated Cost", text=display.strip()).run()
    save_last({
        "models": models,
        "prompt": prompt_text,
        "results": results
    })

if __name__ == "__main__":
    main()

