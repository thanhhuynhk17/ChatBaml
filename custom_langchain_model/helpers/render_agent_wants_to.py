import json
from typing import Optional
def format_args_no_quote_keys(d: dict, indent: Optional[int] = 4) -> str:
    """Pretty JSON-like string with unquoted keys, indent=4"""
    if not d:
        return "{}"
    
    json_str = json.dumps(d, indent=indent, ensure_ascii=False)
    lines = []
    for line in json_str.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('"') and '":' in stripped:
            sp = line[:len(line) - len(stripped)]
            key, rest = stripped.split('":', 1)
            lines.append(f"{sp}{key[1:]}:{rest}")
        else:
            lines.append(line)
    return "\n".join(lines)


# ────────────────────────────────────────────────
# "Agent wants to ..." style templates
# ────────────────────────────────────────────────

def render_agent_wants_to(name: str, arguments: dict, indent: Optional[int]= 2) -> str:
    """
    """
    TEMPLATES = (
        "Tool `{name}` was selected with arguments:\n"
        "{args}"
    )
    args_pretty = format_args_no_quote_keys(arguments, indent=indent)
    
    return TEMPLATES.format(
        name=name,
        args=args_pretty
    )


# ────────────────────────────────────────────────
# Example usage
# ────────────────────────────────────────────────
def main():
    examples = [
        ("CalculatorAdd", {"x": 1, "y": None}),
        ("get_weather", {"location": "Hanoi", "unit": "celsius"}),
        ("search_products", {"query": "wireless earbuds", "min_price": 50, "max_price": 150}),
    ]

    for name, args in examples:
        print("─" * 50)
        print(render_agent_wants_to(name, args))
        print()
        print(render_agent_wants_to(name, args))
        print()
        
if __name__ == "__main__":
    main()