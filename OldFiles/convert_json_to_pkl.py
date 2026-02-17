"""One-time script to convert existing JSON board files to pickle format."""
import json
import pickle
import os
import time

BOARD_DIR = "../board_dicts"

JSON_FILES = [
    "boards_and_scores.json",
    "greedy_boards_and_scores.json",
    "heuristic_boards_and_scores.json",
]

for json_name in JSON_FILES:
    json_path = os.path.join(BOARD_DIR, json_name)
    pkl_path = os.path.join(BOARD_DIR, json_name.replace(".json", ".pkl"))

    if not os.path.exists(json_path):
        print(f"Skipping {json_name} (not found)")
        continue

    print(f"Converting {json_name}...")
    t = time.time()
    with open(json_path, "r") as f:
        data = json.load(f)
    load_time = time.time() - t

    # Convert JSON lists back to tuples for consistency: [count, avg] -> (count, avg)
    for key in data:
        v = data[key]
        if isinstance(v, list):
            data[key] = (v[0], v[1])

    t = time.time()
    with open(pkl_path, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    save_time = time.time() - t

    json_size = os.path.getsize(json_path) / (1024 * 1024)
    pkl_size = os.path.getsize(pkl_path) / (1024 * 1024)

    print(f"  {len(data):,} entries")
    print(f"  JSON: {json_size:.1f} MB (loaded in {load_time:.1f}s)")
    print(f"  PKL:  {pkl_size:.1f} MB (saved in {save_time:.1f}s)")
    print(f"  Size reduction: {(1 - pkl_size / json_size) * 100:.0f}%")
    print()

print("Done! You can now delete the .json files if desired.")
