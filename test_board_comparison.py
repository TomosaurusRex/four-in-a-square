"""
Compare board scores from random (boards_and_scores.json)
and heuristic (heuristic_boards_and_scores.json).
Categorizes boards by score ranges (0-1) and prints statistics.
"""

import json


def load_scores(filepath: str) -> dict:
    """Load JSON file and return {board_key: float_score}."""
    print(f"Loading {filepath}...")
    with open(filepath, "r") as f:
        data = json.load(f)
    print(f"  -> {len(data):,} boards loaded.")
    # Values are [count, score] lists — extract the score (index 1)
    return {k: float(v[1]) if isinstance(v, list) else float(v) for k, v in data.items()}


def categorize(scores: dict) -> dict:
    cats = {"high": 0, "medium_high": 0, "medium_low": 0, "low": 0}
    for s in scores.values():
        if s > 0.8:
            cats["high"] += 1
        elif s > 0.6:
            cats["medium_high"] += 1
        elif s > 0.4:
            cats["medium_low"] += 1
        else:
            cats["low"] += 1
    return cats


LABELS = [
    ("score > 0.8",        "high"),
    ("0.6 < score <= 0.8", "medium_high"),
    ("0.4 < score <= 0.6", "medium_low"),
    ("score <= 0.4",       "low"),
]


def print_table(name: str, cats: dict, total: int):
    print(f"\n{'=' * 60}")
    print(f"  {name}  (total: {total:,})")
    print(f"{'=' * 60}")
    print(f"  {'Score Range':<25} {'Count':>10}   {'%':>7}")
    print(f"  {'-' * 50}")
    for label, key in LABELS:
        c = cats[key]
        pct = c / total * 100 if total else 0
        print(f"  {label:<25} {c:>10,}   {pct:>6.2f}%")
    print(f"  {'-' * 50}")


def print_comparison(r_cats: dict, h_cats: dict, r_total: int, h_total: int):
    print(f"\n{'=' * 80}")
    print(f"  COMPARISON:  Random  vs  Heuristic")
    print(f"{'=' * 80}")
    print(f"  {'Score Range':<25} {'Random':>18}   {'Heuristic':>18}")
    print(f"  {'-' * 70}")
    for label, key in LABELS:
        rc = r_cats[key]
        rp = rc / r_total * 100 if r_total else 0
        hc = h_cats[key]
        hp = hc / h_total * 100 if h_total else 0
        print(f"  {label:<25} {rc:>8,} ({rp:>5.2f}%)   {hc:>8,} ({hp:>5.2f}%)")
    print(f"  {'-' * 70}")


def main():
    random_file    = "board_dicts/boards_and_scores.json"
    heuristic_file = "board_dicts/heuristic_boards_and_scores.json"

    random_scores    = load_scores(random_file)
    heuristic_scores = load_scores(heuristic_file)

    r_cats = categorize(random_scores)
    h_cats = categorize(heuristic_scores)

    print_table("RANDOM PLAYER - Score Distribution",
                r_cats, len(random_scores))
    print_table("HEURISTIC PLAYER - Score Distribution",
                h_cats, len(heuristic_scores))

    print_comparison(r_cats, h_cats,
                     len(random_scores), len(heuristic_scores))

    print(f"\n{'=' * 80}")
    print("  Done!")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
