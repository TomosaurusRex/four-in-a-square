"""
Analyze board score data from pkl files.
Shows score distribution, count distribution, and their interaction —
useful for checking whether temporal decay and data quality need tuning.
"""

import os
import pickle
import statistics


def load_pkl(filepath):
    print(f"Loading {filepath}...")
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    print(f"  -> {len(data):,} boards loaded.")
    return data  # {board_str: (count, avg_score)}


_SCORE_BRACKETS = [
    ("score > 0.8   (Red winning)",    lambda s: s > 0.8),
    ("0.6 < score ≤ 0.8 (Red edge)",  lambda s: 0.6 < s <= 0.8),
    ("0.4 < score ≤ 0.6 (neutral)",   lambda s: 0.4 < s <= 0.6),
    ("0.2 < score ≤ 0.4 (White edge)", lambda s: 0.2 < s <= 0.4),
    ("score ≤ 0.2   (White winning)",  lambda s: s <= 0.2),
]

_COUNT_BRACKETS = [
    ("count = 1",      lambda c: c == 1),
    ("count = 2–3",    lambda c: 2 <= c <= 3),
    ("count = 4–9",    lambda c: 4 <= c <= 9),
    ("count = 10–49",  lambda c: 10 <= c <= 49),
    ("count ≥ 50",     lambda c: c >= 50),
]


def analyze(data, name):
    counts = [v[0] for v in data.values()]
    scores = [v[1] for v in data.values()]
    total = len(data)

    print(f"\n{'=' * 68}")
    print(f"  {name}  (total: {total:,})")
    print(f"{'=' * 68}")

    # --- Score distribution ---
    print(f"\n  Score Distribution:")
    print(f"  {'Range':<38} {'Count':>8}   {'%':>6}")
    print(f"  {'-' * 56}")
    for label, fn in _SCORE_BRACKETS:
        c = sum(1 for s in scores if fn(s))
        print(f"  {label:<38} {c:>8,}   {c / total * 100:>5.1f}%")

    mean_s   = statistics.mean(scores)
    median_s = statistics.median(scores)
    stdev_s  = statistics.stdev(scores)
    print(f"\n  Score stats:  mean={mean_s:.4f}  median={median_s:.4f}  stdev={stdev_s:.4f}")

    # --- Count distribution with avg score per bracket ---
    print(f"\n  Count Distribution  (how often each board was seen):")
    print(f"  {'Range':<18} {'Boards':>8}   {'%':>6}   {'Avg Score':>10}   {'Score Stdev':>11}")
    print(f"  {'-' * 62}")
    for label, fn in _COUNT_BRACKETS:
        subset_scores = [s for c, s in zip(counts, scores) if fn(c)]
        if not subset_scores:
            continue
        avg_s = statistics.mean(subset_scores)
        sd_s  = statistics.stdev(subset_scores) if len(subset_scores) > 1 else 0.0
        print(f"  {label:<18} {len(subset_scores):>8,}   "
              f"{len(subset_scores) / total * 100:>5.1f}%   "
              f"{avg_s:>10.4f}   {sd_s:>11.4f}")

    mean_c   = statistics.mean(counts)
    median_c = statistics.median(counts)
    print(f"\n  Count stats:  mean={mean_c:.1f}  median={median_c}  max={max(counts)}")

    # --- Min-count filter impact ---
    print(f"\n  Min-count filter impact (boards that survive each threshold):")
    print(f"  {'Threshold':<15} {'Boards kept':>12}   {'% of total':>10}")
    print(f"  {'-' * 42}")
    for thresh in (1, 2, 3, 5, 10):
        kept = sum(1 for c in counts if c >= thresh)
        print(f"  min_count ≥ {thresh:<4} {kept:>12,}   {kept / total * 100:>9.1f}%")

    # --- Decay note ---
    print(f"\n  Decay note:")
    print(f"  Scores near 0.5 ({sum(1 for s in scores if 0.4 < s <= 0.6):,} boards, "
          f"{sum(1 for s in scores if 0.4 < s <= 0.6) / total * 100:.1f}%) "
          f"provide weak training signal.")
    print(f"  Polarized boards (>0.8 or ≤0.2): "
          f"{sum(1 for s in scores if s > 0.8 or s <= 0.2):,} "
          f"({sum(1 for s in scores if s > 0.8 or s <= 0.2) / total * 100:.1f}%)")


def compare(data1, name1, data2, name2):
    scores1 = [v[1] for v in data1.values()]
    scores2 = [v[1] for v in data2.values()]
    t1, t2 = len(scores1), len(scores2)

    n1 = name1[:16]
    n2 = name2[:16]
    print(f"\n{'=' * 80}")
    print(f"  COMPARISON:  {name1}  vs  {name2}")
    print(f"{'=' * 80}")
    print(f"  {'Range':<38} {n1:>16}   {n2:>16}")
    print(f"  {'-' * 76}")
    for label, fn in _SCORE_BRACKETS:
        c1 = sum(1 for s in scores1 if fn(s))
        c2 = sum(1 for s in scores2 if fn(s))
        print(f"  {label:<38} {c1:>6,} ({c1/t1*100:>5.1f}%)   {c2:>6,} ({c2/t2*100:>5.1f}%)")


def main():
    candidates = {
        "Heuristic": "board_dicts/heuristic_boards_and_scores.pkl",
        "Random":    "board_dicts/boards_and_scores.pkl",
        "Greedy":    "board_dicts/greedy_boards_and_scores.pkl",
    }

    loaded = {}
    for name, path in candidates.items():
        if os.path.exists(path):
            loaded[name] = load_pkl(path)
        else:
            print(f"  {name}: {path} not found, skipping.")

    for name, data in loaded.items():
        analyze(data, name)

    names = list(loaded.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            compare(loaded[names[i]], names[i], loaded[names[j]], names[j])

    print(f"\n{'=' * 68}")
    print("  Done.")
    print(f"{'=' * 68}\n")


if __name__ == "__main__":
    main()
