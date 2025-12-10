"""
Improved Token & Cost Estimator for Claude and Gemini
(using heuristic-based token estimation: character‑based or word‑based)

Important: This is only an estimate. Actual token counts may differ.
"""

import json
import math
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, message_dialog

# --- Pricing (USD per 1M tokens) for input and output ---
PRICING = {
    "claude": {"input_per_m": 3.00, "output_per_m": 15.00},
    "gemini": {"input_per_m": 1.25, "output_per_m": 10.00},
}

# USD → EUR conversion rate (adjust to current rate)
USD_TO_EUR = 0.92

def estimate_tokens_by_chars(text: str) -> int:
    """Estimate tokens based on character count. Approx 1 token ≈ 4 chars (English)."""
    chars = len(text)
    return max(1, math.ceil(chars / 4))

def estimate_tokens_by_words(text: str) -> int:
    """Estimate tokens based on word count. Approx 1 token ≈ 0.75 word."""
    words = len(text.split())
    # token ≈ words / 0.75  → token = words * (1 / 0.75) ≈ words * 1.333
    return max(1, int(words * 1.333))

def deduce_output_tokens(prompt_tokens: int) -> int:
    """
    Heuristic to guess output length:
      - Very short prompts → maybe longer output → 2× prompt_tokens
      - Medium → 1× prompt_tokens
      - Long prompts → shorter relative output → 0.5× prompt_tokens
    """
    if prompt_tokens < 50:
        return prompt_tokens * 2
    elif prompt_tokens <= 500:
        return prompt_tokens
    else:
        return int(prompt_tokens * 0.5)

def calculate_cost(tokens_input: int, tokens_output: int, model: str):
    """Calculate estimated cost in EUR for given token counts."""
    price = PRICING.get(model)
    if price is None:
        return 0.0
    cost_usd = (tokens_input / 1_000_000) * price["input_per_m"]
    cost_usd += (tokens_output / 1_000_000) * price["output_per_m"]
    cost_eur = cost_usd * USD_TO_EUR
    return float(f"{cost_eur:.8f}")

def main():
    models = checkboxlist_dialog(
        title="Select Model(s)",
        text="Which model(s) to estimate for?",
        values=[("claude", "Claude"), ("gemini", "Gemini")]
    ).run()
    if not models:
        message_dialog(title="No model selected", text="Exiting.").run()
        return

    prompt_text = input_dialog(
        title="Prompt Text",
        text="Enter your prompt (multi-line allowed):"
    ).run()
    if not prompt_text or not prompt_text.strip():
        message_dialog(title="Error", text="Prompt is empty — exiting.").run()
        return

    # Estimate tokens by both chars and words
    tokens_chars = estimate_tokens_by_chars(prompt_text)
    tokens_words = estimate_tokens_by_words(prompt_text)
    # Choose which estimate to use (you could allow user choice, here use average)
    prompt_tokens = int((tokens_chars + tokens_words) / 2)

    # Deduce output tokens
    output_tokens = deduce_output_tokens(prompt_tokens)

    results = {}
    for m in models:
        cost = calculate_cost(prompt_tokens, output_tokens, m)
        results[m] = {
            "input_tokens_estimate": prompt_tokens,
            "output_tokens_estimate": output_tokens,
            "estimated_cost_eur": cost
        }

    # Build display text
    display = (
        "Token estimation method: average of char-based and word-based heuristics\n\n"
    )
    for m, r in results.items():
        display += (
            f"{m.title()}:\n"
            f"  Estimated Input Tokens: {r['input_tokens_estimate']}\n"
            f"  Estimated Output Tokens: {r['output_tokens_estimate']}\n"
            f"  Estimated Total Cost (EUR): €{r['estimated_cost_eur']}\n\n"
        )
    display += "⚠️ Note: This is only an estimate. Actual token counts and costs may differ."

    message_dialog(title="Estimated Cost (Heuristic)", text=display).run()

    # Optionally save results
    with open("last_estimate.json", "w", encoding="utf-8") as f:
        json.dump({
            "models": models,
            "prompt": prompt_text,
            "input_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "results": results
        }, f, indent=2)

if __name__ == "__main__":
    main()

