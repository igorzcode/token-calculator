"""
Retro-Styled Coding Project Token & Cost Estimator for Claude and Gemini

Features:
- Automatic iteration estimation based on prompt length & coding keywords
- Input/output token estimation with realistic multipliers
- Retro dark gray background with muted olive green text
- Master prompt input box: gray text, truncated instead of scrolling
- Saves last calculation to last_estimate.json
"""

import json
import math
from prompt_toolkit import print_formatted_text, prompt
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.key_binding import KeyBindings

# --- Pricing ---
PRICING = {
    "claude": {"input_per_m": 3.00, "output_per_m": 15.00},
    "gemini": {"input_per_m": 1.25, "output_per_m": 10.00},
}
USD_TO_EUR = 0.92

# --- Coding keywords ---
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

# --- Retro UI Style ---
retro_style = Style.from_dict({
    "dialog": "bg:#2e2e2e",
    "dialog.frame-label": "bg:#2e2e2e #9aa65e bold",
    "dialog.body": "bg:#2e2e2e #9aa65e",
    "dialog.shadow": "bg:#1c1c1c",
    "button": "bg:#2e2e2e #9aa65e",
    "button.focused": "bg:#9aa65e #2e2e2e bold",
    "checkbox": "#9aa65e",
    "checkbox.focused": "bg:#9aa65e #2e2e2e bold",
    "input.text": "bg:#2e2e2e #c0c0c0",  # gray text for input
})

# --- Token estimation functions ---
def estimate_tokens_by_chars(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))

def estimate_tokens_by_words(text: str) -> int:
    words = len(text.split())
    return max(1, int(words / 0.75))

def estimate_input_tokens(prompt_text: str) -> int:
    tokens_chars = estimate_tokens_by_chars(prompt_text)
    tokens_words = estimate_tokens_by_words(prompt_text)
    return int((tokens_chars + tokens_words) / 2)

def deduce_iterations(prompt_text: str, prompt_tokens: int) -> int:
    prompt_lower = prompt_text.lower()
    if prompt_tokens < 50:
        base_iterations = 2
    elif prompt_tokens <= 200:
        base_iterations = 5
    else:
        base_iterations = 15
    keyword_hits = sum(1 for kw in CODING_KEYWORDS if kw in prompt_lower)
    return max(1, base_iterations + keyword_hits)

def estimate_output_tokens_per_iteration(prompt_tokens: int) -> int:
    if prompt_tokens < 50:
        multiplier = 10
    elif prompt_tokens <= 200:
        multiplier = 8
    else:
        multiplier = 5
    return int(prompt_tokens * multiplier)

def calculate_cost(tokens_input: int, tokens_output: int, model: str) -> float:
    price = PRICING.get(model)
    if not price:
        return 0.0
    cost_usd = (tokens_input / 1_000_000) * price["input_per_m"]
    cost_usd += (tokens_output / 1_000_000) * price["output_per_m"]
    return float(f"{cost_usd * USD_TO_EUR:.8f}")

def save_last(data: dict):
    with open("last_estimate.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- Main Program ---
def main():
    # Model selection
    models = checkboxlist_dialog(
        title="Select Model(s)",
        text="Which model(s) to estimate for?",
        values=[("claude", "Claude"), ("gemini", "Gemini")],
        style=retro_style
    ).run()
    if not models:
        print_formatted_text(FormattedText([("class:dialog.body", "No model selected. Exiting.\n")]), style=retro_style)
        return

    # Master prompt input: gray text and truncate input
    bindings = KeyBindings()
    # Disable multi-line, just truncate
    def handle_enter(event):
        event.app.exit(result=event.app.current_buffer.text)
    bindings.add("enter")(handle_enter)

    prompt_text = prompt(
        "Enter your master coding prompt: ",
        style=retro_style,
        key_bindings=bindings,
        multiline=False,         # truncate instead of wrapping
        wrap_lines=False
    )

    if not prompt_text or not prompt_text.strip():
        print_formatted_text(FormattedText([("class:dialog.body", "Prompt is empty. Exiting.\n")]), style=retro_style)
        return

    # Token estimation
    input_tokens = estimate_input_tokens(prompt_text)
    iterations = deduce_iterations(prompt_text, input_tokens)
    output_tokens_per_iter = estimate_output_tokens_per_iteration(input_tokens)
    total_output_tokens = output_tokens_per_iter * iterations
    total_input_tokens = input_tokens * iterations  # assume CLI prompts similar size

    # Calculate costs
    results = {}
    for m in models:
        cost = calculate_cost(total_input_tokens, total_output_tokens, m)
        results[m] = {
            "estimated_iterations": iterations,
            "input_tokens_per_prompt": input_tokens,
            "total_input_tokens": total_input_tokens,
            "output_tokens_per_iteration": output_tokens_per_iter,
            "total_output_tokens": total_output_tokens,
            "estimated_cost_eur": cost
        }

    # Prepare display
    display_lines = []
    display_lines.append("⚠️ Estimated Total Coding Session Cost")
    display_lines.append("Heuristic: iterations & output tokens deduced from prompt length & keywords.\n")
    for m, r in results.items():
        display_lines.append(f"{m.title()}:")
        display_lines.append(f"  Estimated Iterations: {r['estimated_iterations']}")
        display_lines.append(f"  Input Tokens per Prompt: {r['input_tokens_per_prompt']}")
        display_lines.append(f"  Total Input Tokens: {r['total_input_tokens']}")
        display_lines.append(f"  Output Tokens per Iteration: {r['output_tokens_per_iteration']}")
        display_lines.append(f"  Total Output Tokens: {r['total_output_tokens']}")
        display_lines.append(f"  Estimated Total Cost (EUR): €{r['estimated_cost_eur']}\n")

    # Display results
    styled_lines = [("class:dialog.body", line + "\n") for line in display_lines]
    print_formatted_text(FormattedText(styled_lines), style=retro_style)

    # Save last calculation
    save_last({
        "models": models,
        "prompt": prompt_text,
        "results": results
    })

if __name__ == "__main__":
    main()

