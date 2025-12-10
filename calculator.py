"""
Claude and Gemini Token & Cost Calculator
Author: Your Name
Date: 2025-12-10

This script estimates the token usage and cost for Claude and Gemini models
based on user-provided prompts and euro-per-token rates.

Features:
- Step-by-step TUI using prompt_toolkit
- Multi-line prompt input
- Approximate token counting per model
- Cost estimation
- Optional: estimate tokens for the final response
- Saves last calculation to a local file
"""

import json
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, message_dialog

# ---------------------------
# Token Counting Functions
# ---------------------------

def count_tokens_claude(prompt_text: str) -> int:
    """
    Approximate token count for Claude.
    Assumes ~1.3 tokens per word.
    """
    words = len(prompt_text.split())
    tokens = int(words * 1.3)
    return tokens

def count_tokens_gemini(prompt_text: str) -> int:
    """
    Approximate token count for Gemini.
    Assumes ~1.1 tokens per word.
    """
    words = len(prompt_text.split())
    tokens = int(words * 1.1)
    return tokens

# ---------------------------
# Cost Calculation
# ---------------------------

def calculate_cost(tokens: int, euro_per_token: float) -> float:
    """Calculate estimated cost in euros."""
    return round(tokens * euro_per_token, 4)

# ---------------------------
# Save last calculation
# ---------------------------

def save_last_calculation(data: dict):
    """Save last calculation to a local JSON file."""
    with open("last_calculation.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------------------
# Main TUI Logic
# ---------------------------

def main():
    # Step 1: Select models
    models = checkboxlist_dialog(
        title="Select Models",
        text="Which model(s) do you want to calculate for?",
        values=[("claude", "Claude"), ("gemini", "Gemini")],
    ).run()

    if not models:
        message_dialog(title="Error", text="No models selected. Exiting.").run()
        return

    # Step 2: Get euro-per-token rates
    euro_rates = {}
    for model in models:
        rate = input_dialog(
            title=f"{model.title()} Euro-per-Token",
            text=f"Enter euro-per-token rate for {model.title()}:"
        ).run()
        try:
            euro_rates[model] = float(rate)
        except ValueError:
            message_dialog(title="Error", text="Invalid rate. Exiting.").run()
            return

    # Step 3: Get user prompt (multi-line)
    prompt_text = input_dialog(
        title="Enter Prompt",
        text="Enter your prompt (multi-line allowed):"
    ).run()

    if not prompt_text.strip():
        message_dialog(title="Error", text="Prompt is empty. Exiting.").run()
        return

    # Optional: Max response tokens
    max_response = input_dialog(
        title="Max Response Tokens",
        text="Optional: enter expected max tokens for the model response (or leave blank):"
    ).run()
    try:
        max_response_tokens = int(max_response) if max_response.strip() else 0
    except ValueError:
        max_response_tokens = 0

    # Step 4: Calculate tokens and cost
    results = {}
    for model in models:
        if model == "claude":
            tokens_prompt = count_tokens_claude(prompt_text)
        elif model == "gemini":
            tokens_prompt = count_tokens_gemini(prompt_text)
        else:
            tokens_prompt = 0

        total_tokens = tokens_prompt + max_response_tokens
        cost = calculate_cost(total_tokens, euro_rates[model])
        results[model] = {
            "prompt_tokens": tokens_prompt,
            "response_tokens": max_response_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_eur": cost
        }

    # Step 5: Display results
    result_text = ""
    for model, data in results.items():
        result_text += (
            f"{model.title()}:\n"
            f"  Prompt Tokens: {data['prompt_tokens']}\n"
            f"  Response Tokens: {data['response_tokens']}\n"
            f"  Total Tokens: {data['total_tokens']}\n"
            f"  Estimated Cost (€): {data['estimated_cost_eur']}\n\n"
        )

    message_dialog(title="Estimated Costs", text=result_text.strip()).run()

    # Step 6: Save last calculation
    save_last_calculation({
        "models": models,
        "euro_rates": euro_rates,
        "prompt": prompt_text,
        "max_response_tokens": max_response_tokens,
        "results": results
    })

if __name__ == "__main__":
    main()
