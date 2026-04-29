from game import FourInASquareGame


class Tournament:
    """
    Run several games and save their results
    """

    def __init__(self):
        print("How many games do you want to play? ", end='', flush=True)
        self.games_number = int(input())
        print("\nChoose mode:", flush=True)
        print("1. Random", flush=True)
        print("2. Greedy on random json (boards_and_scores.json)", flush=True)
        print("3. Greedy on greedy json (greedy_boards_and_scores.json)", flush=True)
        print("4. Heuristic (uses greedy json for greedy moves, saves to heuristic json)", flush=True)
        print("5. Heuristic vs Heuristic (saves to heuristic json)", flush=True)
        print("Enter choice (1, 2, 3, 4, or 5): ", end='', flush=True)
        choice = input().strip()
        
        self.stats_dict = {"Red wins": 0, "White wins": 0, "Draw": 0}
        
        # Set up play mode and file paths based on choice
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
        else:
            print("Invalid choice, defaulting to Random")
            self.play_mode = "RANDOM"
            self.load_file = "board_dicts/boards_and_scores.pkl"
            self.save_file = "board_dicts/boards_and_scores.pkl"
            self.greedy_file = "board_dicts/greedy_boards_and_scores.pkl"

    def run_games(self):
        # Clear new_boards and load the learning data
        FourInASquareGame.new_boards = {}
        FourInASquareGame.greedy_boards = {}
        FourInASquareGame.total_greedy_moves = 0
        FourInASquareGame.random_fallback_moves = 0
        
        # Create one game instance and reuse it
        game = FourInASquareGame(self.play_mode, load_file=self.load_file, save_file=self.save_file, greedy_file=self.greedy_file)
        initial_boards = len(FourInASquareGame.learning_boards)
        
        for i in range(self.games_number):
            if (i + 1) % 1000 == 0 or i == 0:
                print(f"Game {i + 1}/{self.games_number}")

            game.play()
            
            result = game.check_win()
            if result in self.stats_dict:
                self.stats_dict[result] += 1
            
            game.save_game_to_dict()
            game.reset_game()
        
        # Save once at the end
        FourInASquareGame.save_all_to_file(self.save_file)
        
        # Count boards from memory (no extra file read)
        self.total_boards = len(FourInASquareGame.learning_boards)
        self.new_boards_learned = self.total_boards - initial_boards

    def print_tournament_result(self):
        print(f"\nResults for {self.games_number} games ({self.play_mode} mode):")
        print(f"Red wins: {self.stats_dict['Red wins']} ({self.stats_dict['Red wins'] / self.games_number * 100:.1f}%)")
        print(f"White wins: {self.stats_dict['White wins']} ({self.stats_dict['White wins'] / self.games_number * 100:.1f}%)")
        print(f"Draws: {self.stats_dict['Draw']} ({self.stats_dict['Draw'] / self.games_number * 100:.1f}%)")
        
        print(f"\nTotal board states in {self.save_file}: {self.total_boards}")
        print(f"New boards learned during this tournament: {self.new_boards_learned}")
        
        if self.play_mode == "GREEDY" and FourInASquareGame.total_greedy_moves > 0:
            fallback_percentage = (FourInASquareGame.random_fallback_moves / FourInASquareGame.total_greedy_moves) * 100
            print(f"\nGreedy Agent Statistics:")
            print(f"Total greedy moves attempted: {FourInASquareGame.total_greedy_moves}")
            print(f"Random fallback moves (board not found): {FourInASquareGame.random_fallback_moves} ({fallback_percentage:.2f}%)")


if __name__ == "__main__":
    tournament = Tournament()
    tournament.run_games()
    tournament.print_tournament_result()




