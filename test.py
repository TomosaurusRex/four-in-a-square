import json

# Load and count entries in boards_and_scores.json
with open('boards_and_scores.json', 'r') as f:
    boards_and_scores = json.load(f)
    print(f"boards_and_scores.json has {len(boards_and_scores)} entries")

# Load and count entries in greedy_boards_and_scores.json
with open('greedy_boards_and_scores.json', 'r') as f:
    greedy_boards_and_scores = json.load(f)
    print(f"greedy_boards_and_scores.json has {len(greedy_boards_and_scores)} entries")
