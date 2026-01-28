from game import FourInASquareGame
import json


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
        print("Enter choice (1, 2, 3, or 4): ", end='', flush=True)
        choice = input().strip()
        
        self.stats_dict = {"Red wins": 0, "White wins": 0, "Draw": 0}
        
        # Set up play mode and file paths based on choice
        if choice == "1":
            self.play_mode = "RANDOM"
            self.load_file = "boards_and_scores.json"
            self.save_file = "boards_and_scores.json"
            self.greedy_file = "greedy_boards_and_scores.json"
        elif choice == "2":
            self.play_mode = "GREEDY"
            self.load_file = "boards_and_scores.json"
            self.save_file = "greedy_boards_and_scores.json"
            self.greedy_file = "greedy_boards_and_scores.json"
        elif choice == "3":
            self.play_mode = "GREEDY"
            self.load_file = "greedy_boards_and_scores.json"
            self.save_file = "greedy_boards_and_scores.json"
            self.greedy_file = "greedy_boards_and_scores.json"
        elif choice == "4":
            self.play_mode = "HEURISTIC"
            self.load_file = "heuristic_boards_and_scores.json"
            self.save_file = "heuristic_boards_and_scores.json"
            self.greedy_file = "greedy_boards_and_scores.json"
        else:
            print("Invalid choice, defaulting to Random")
            self.play_mode = "RANDOM"
            self.load_file = "boards_and_scores.json"
            self.save_file = "boards_and_scores.json"
            self.greedy_file = "greedy_boards_and_scores.json"

    def run_games(self):
        # Load initial boards from save file only
        try:
            with open(self.save_file, "r") as f:
                initial_save_data = json.load(f)
                initial_boards = len(initial_save_data)
        except FileNotFoundError:
            initial_boards = 0
        
        # Clear new_boards and load the learning data
        FourInASquareGame.new_boards = {}
        FourInASquareGame.greedy_boards = {}
        FourInASquareGame.total_greedy_moves = 0
        FourInASquareGame.random_fallback_moves = 0
        dummy = FourInASquareGame(self.play_mode, load_json_file=self.load_file, save_json_file=self.save_file, greedy_json_file=self.greedy_file)
        
        for i in range(self.games_number):
            if (i + 1) % 1000 == 0 or i == 0:
                print(f"Game {i + 1}/{self.games_number}")

            game = FourInASquareGame(self.play_mode, load_json_file=self.load_file, save_json_file=self.save_file, greedy_json_file=self.greedy_file)
            game.play()
            
            result = game.check_win()
            if result in self.stats_dict:
                self.stats_dict[result] += 1
            
            game.save_game_to_dict()
        
        # Save once at the end
        FourInASquareGame.save_all_to_file(self.save_file)
        
        # Count final boards from save file
        with open(self.save_file, "r") as f:
            final_save_data = json.load(f)
            final_boards = len(final_save_data)
        
        self.new_boards_learned = final_boards - initial_boards
        self.total_boards = final_boards

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




