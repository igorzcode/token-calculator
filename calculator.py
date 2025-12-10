"""
Advanced Coding Project Token & Cost Estimator for Claude and Gemini

Estimates total session cost based on a single master prompt, automatically
estimating iterations and output tokens for coding projects.
"""

import json
import math
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, message_dialog

# --- Pricing (USD per 1M tokens) ---
PRICING = {
    "claude": {"input_per_m": 3.00, "output_per_m": 15.00},
    "gemini": {"input_per_m": 1.25, "output_per_m": 10.00},
}

USD_TO_EUR = 0.92

# --- Coding / development keywords ---
CODING_KEYWORDS = [
    "code", "function", "script", "class", "module", "package",
    "algorithm", "refactor", "optimize", "debug", "compile", 
    "build", "deploy", "test", "integration", "unit test",
    "syntax", "variable", "loop", "recursion", "data structure",
    "api", "endpoint", "database", "sql", "json", "xml",
    "frontend", "backend", "ui", "ux", "framework", "library",
    "performance", "scalability", "architecture", "ci/cd", "pipeline",
    "exception", "error handling", "logging", "thread", "concurrency",
    "threading", "async", "await", "docker", "container", "microservice",
    "refactoring", "optimization", "version control", "git", "merge", "branch"
]

# --- Functions ---
def estimate_tokens_by_chars(text: str) -> int:
    """Estimate tokens based on character count (1 token ≈ 4 chars)."""
    return max(1, math.ceil(len(text) / 4))

def estimate_tokens_by_words(text: str) -> int:
    """Estimate tokens based on word count (1 token ≈ 0.75 words)."""
    words = len(text.split())
    return max(1, int(words / 0.75))

def estimate_input_tokens(prompt_text: str) -> int:
    """Average char-based and word-based token estimates."""
    tokens_chars = estimate_tokens_by_chars(prompt_text)
    tokens_words = estimate_tokens_by_words(prompt_text)
    return int((tokens_chars + tokens_words) / 2)

def deduce_iterations(prompt_text: str, prompt_tokens: int) -> int:
    """Estimate number of iterations based on prompt length and coding keywords."""
    prompt_lower = prompt_text.lower()

    # Base iterations from prompt length
    if prompt_tokens < 50:
        base_iterations = 2
    elif prompt_tokens <= 200:
        base_iterations = 5
    else:
        base_iterations = 15

    # Extra iterations from coding keywords
    keyword_hits = sum(1 for kw in CODING_KEYWORDS if kw in prompt_lower)
    estimated_iterations = base_iterations + keyword_hits
    return max(1, estimated_iterations)

def estimate_output_tokens_per_iteration(prompt_tokens: int) -> int:
    """Estimate output tokens per iteration (coding projects often produce much more output)."""
    if prompt_tokens < 50:
        multiplier = 10
    elif prompt_tokens <= 200:
        multiplier = 8
    else:
        multiplier = 5
    return int(prompt_tokens * multiplier)

def calculate_cost(tokens_input: int, tokens_output: int, model: str) -> float:
    """Calculate estimated cost in EUR."""
    price = PRICING.get(model)
    if not price:
        return 0.0
    cost_usd = (tokens_input / 1_000_000) * price["input_per_m"]
    cost_usd += (tokens_output / 1_000_000) * price["output_per_m"]
    cost_eur = cost_usd * USD_TO_EUR
    return float(f"{cost_eur:.8f}")

def save_last(data: dict):
    with open("last_estimate.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- Main Program ---
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
        title="Master Prompt",
        text="Enter your master coding prompt (multi-line allowed):"
    ).run()
    if not prompt_text or not prompt_text.strip():
        message_dialog(title="Error", text="Prompt is empty — exiting.").run()
        return

    # Estimate input tokens
    input_tokens = estimate_input_tokens(prompt_text)

    # Estimate iterations
    iterations = deduce_iterations(prompt_text, input_tokens)

    # Estimate output tokens per iteration
    output_tokens_per_iter = estimate_output_tokens_per_iteration(input_tokens)
    total_output_tokens = output_tokens_per_iter * iterations

    results = {}
    for m in models:
        total_input_tokens = input_tokens + (input_tokens * (iterations - 1))  # assume CLI prompts similar
        cost = calculate_cost(total_input_tokens, total_output_tokens, m)
        results[m] = {
            "estimated_iterations": iterations,
            "input_tokens_per_prompt": input_tokens,
            "total_input_tokens": total_input_tokens,
            "output_tokens_per_iteration": output_tokens_per_iter,
            "total_output_tokens": total_output_tokens,
            "estimated_cost_eur": cost
        }

    # Display results
    display = "⚠️ Note: This is an estimated cost for the full coding session.\n"
    display += "Heuristic: iterations and output tokens deduced from prompt length and keywords.\n\n"

    for m, r in results.items():
        display += (
            f"{m.title()}:\n"
            f"  Estimated Iterations: {r['estimated_iterations']}\n"
            f"  Input Tokens per Prompt: {r['input_tokens_per_prompt']}\n"
            f"  Total Input Tokens: {r['total_input_tokens']}\n"
            f"  Output Tokens per Iteration: {r['output_tokens_per_iteration']}\n"
            f"  Total Output Tokens: {r['total_output_tokens']}\n"
            f"  Estimated Total Cost (EUR): €{r['estimated_cost_eur']}\n\n"
        )

    message_dialog(title="Estimated Total Coding Session Cost", text=display.strip()).run()

    save_last({
        "models": models,
        "prompt": prompt_text,
        "results": results
    })

if __name__ == "__main__":
    main()

