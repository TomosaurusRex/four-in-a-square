import os
import pickle
import multiprocessing as mp
from game import FourInASquareGame


def _worker(args):
    """Run a batch of games in a worker process.
    Returns (new_boards, stats, total_greedy_moves, random_fallback_moves).
    """
    num_games, play_mode, load_file, save_file, greedy_file, exploration_rate, seed, worker_id = args

    import random
    random.seed(seed)

    # Each spawned process starts fresh; reset defensively in case of reuse
    FourInASquareGame.learning_boards = {}
    FourInASquareGame.new_boards = {}
    FourInASquareGame.total_greedy_moves = 0
    FourInASquareGame.random_fallback_moves = 0
    FourInASquareGame._nn_model = None
    FourInASquareGame._nn_model_loaded = False

    game = FourInASquareGame(play_mode, load_file, save_file, greedy_file, exploration_rate)

    stats = {"Red wins": 0, "White wins": 0, "Draw": 0}

    for i in range(num_games):
        if (i + 1) % 5000 == 0:
            print(f"  Worker {worker_id}: {i + 1}/{num_games} games done", flush=True)

        game.play()
        result = game.check_win()
        if result in stats:
            stats[result] += 1
        game.reset_game()

    return (
        dict(FourInASquareGame.new_boards),
        stats,
        FourInASquareGame.total_greedy_moves,
        FourInASquareGame.random_fallback_moves,
    )


def _merge_boards(target, source):
    """Merge source board dict into target in-place (weighted average)."""
    for key, (count, avg) in source.items():
        if key in target:
            t_count, t_avg = target[key]
            new_count = t_count + count
            target[key] = (new_count, (t_avg * t_count + avg * count) / new_count)
        else:
            target[key] = (count, avg)


class Tournament:
    """Run several games in parallel and save their results."""

    def __init__(self):
        print("How many games do you want to play? ", end='', flush=True)
        self.games_number = int(input())
        print("\nChoose mode:", flush=True)
        print("1. Random", flush=True)
        print("2. Greedy on random json (boards_and_scores.json)", flush=True)
        print("3. Greedy on greedy json (greedy_boards_and_scores.json)", flush=True)
        print("4. Heuristic (uses greedy json for greedy moves, saves to heuristic json)", flush=True)
        print("5. Heuristic vs Heuristic (saves to heuristic json)", flush=True)
        print("6. Neural Net vs Random (no saving)", flush=True)
        print("7. Neural Net vs Heuristic (no saving)", flush=True)
        print("Enter choice (1, 2, 3, 4, 5, 6, or 7): ", end='', flush=True)
        choice = input().strip()

        self.stats_dict = {"Red wins": 0, "White wins": 0, "Draw": 0}

        if choice == "1":
            self.play_mode = "RANDOM"
            self.load_file = "board_dicts/boards_and_scores.pkl"
            self.save_file = "board_dicts/boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"
        elif choice == "2":
            self.play_mode = "GREEDY"
            self.load_file = "board_dicts/boards_and_scores.pkl"
            self.save_file = "board_dicts/greedy_boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"
        elif choice == "3":
            self.play_mode = "GREEDY"
            self.load_file = "board_dicts/greedy_boards_and_scores.pkl"
            self.save_file = "board_dicts/greedy_boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"
        elif choice == "4":
            self.play_mode = "HEURISTIC"
            self.load_file = "board_dicts/heuristic_boards_and_scores.pkl"
            self.save_file = "board_dicts/heuristic_boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"
        elif choice == "5":
            self.play_mode = "HEURISTIC_VS_HEURISTIC"
            self.load_file = "board_dicts/heuristic_boards_and_scores.pkl"
            self.save_file = "board_dicts/heuristic_boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"
        elif choice == "6":
            self.play_mode = "NN_VS_RANDOM"
            self.load_file = None
            self.save_file = None
            self.greedy_file = None
        elif choice == "7":
            self.play_mode = "NN_VS_HEURISTIC"
            self.load_file = None
            self.save_file = None
            self.greedy_file = None
        else:
            print("Invalid choice, defaulting to Random")
            self.play_mode = "RANDOM"
            self.load_file = "board_dicts/boards_and_scores.pkl"
            self.save_file = "board_dicts/boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"

    def run_games(self):
        nn_mode = self.play_mode in ("NN_VS_RANDOM", "NN_VS_HEURISTIC")

        load_file = self.load_file or "board_dicts/boards_and_scores.pkl"
        save_file = self.save_file or "board_dicts/boards_and_scores.pkl"
        greedy_file = self.greedy_file or "board_dicts/greedy_boards_and_scores.pkl"

        # Load existing boards in the main process before workers start
        existing_boards = {}
        if not nn_mode and os.path.exists(load_file):
            with open(load_file, "rb") as f:
                existing_boards = pickle.load(f)
        initial_count = len(existing_boards)

        # Use physical cores (half of logical on hyperthreaded CPUs) — CPU-bound work
        # gets no benefit from hyperthreading and doubling workers doubles memory use.
        num_workers = min(max(1, mp.cpu_count() // 2), self.games_number)
        base = self.games_number // num_workers
        remainder = self.games_number % num_workers
        worker_counts = [base + (1 if i < remainder else 0) for i in range(num_workers)]

        import random as _random
        args_list = [
            (n, self.play_mode, load_file, save_file, greedy_file, 0.1, _random.randint(0, 2**31), i)
            for i, n in enumerate(worker_counts)
            if n > 0
        ]

        print(f"\nRunning {self.games_number} games across {num_workers} workers...", flush=True)

        with mp.Pool(num_workers) as pool:
            results = pool.map(_worker, args_list)

        # Merge all worker results into one dict
        merged_new = {}
        total_greedy = 0
        total_fallback = 0

        for new_boards, worker_stats, greedy_moves, fallback_moves in results:
            _merge_boards(merged_new, new_boards)
            for k in self.stats_dict:
                self.stats_dict[k] += worker_stats.get(k, 0)
            total_greedy += greedy_moves
            total_fallback += fallback_moves

        FourInASquareGame.total_greedy_moves = total_greedy
        FourInASquareGame.random_fallback_moves = total_fallback

        # Save merged result once (skip for NN_VS_RANDOM)
        if not nn_mode:
            FourInASquareGame.learning_boards = existing_boards
            FourInASquareGame.new_boards = merged_new
            FourInASquareGame.save_all_to_file(self.save_file)
            self.total_boards = len(existing_boards)  # save_all_to_file merges into this dict
            self.new_boards_learned = self.total_boards - initial_count
        else:
            self.total_boards = 0
            self.new_boards_learned = 0

    def print_tournament_result(self):
        print(f"\nResults for {self.games_number} games ({self.play_mode} mode):")
        print(f"Red wins: {self.stats_dict['Red wins']} ({self.stats_dict['Red wins'] / self.games_number * 100:.1f}%)")
        print(f"White wins: {self.stats_dict['White wins']} ({self.stats_dict['White wins'] / self.games_number * 100:.1f}%)")
        print(f"Draws: {self.stats_dict['Draw']} ({self.stats_dict['Draw'] / self.games_number * 100:.1f}%)")

        if self.play_mode not in ("NN_VS_RANDOM", "NN_VS_HEURISTIC"):
            print(f"\nTotal board states in {self.save_file}: {self.total_boards}")
            print(f"New boards learned during this tournament: {self.new_boards_learned}")

        if self.play_mode == "GREEDY" and FourInASquareGame.total_greedy_moves > 0:
            fallback_pct = (FourInASquareGame.random_fallback_moves / FourInASquareGame.total_greedy_moves) * 100
            print(f"\nGreedy Agent Statistics:")
            print(f"Total greedy moves attempted: {FourInASquareGame.total_greedy_moves}")
            print(f"Random fallback moves (board not found): {FourInASquareGame.random_fallback_moves} ({fallback_pct:.2f}%)")


if __name__ == "__main__":
    tournament = Tournament()
    tournament.run_games()
    tournament.print_tournament_result()
