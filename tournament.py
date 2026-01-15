from game import FourInASquareGame
import json


class Tournament:
    """
    Run several games and save their results
    """

    def __init__(self):
        self.games_number = int(input("How many games do you want to play? "))
        self.play_mode = input("RANDOM or GREEDY: ").strip().upper()
        self.stats_dict = {"Red wins": 0, "White wins": 0, "Draw": 0}
        
        # Set up file paths based on mode
        if self.play_mode == "GREEDY":
            self.load_file = "boards_and_scores.json"
            self.save_file = "greedy_boards_and_scores.json"
        else:
            self.load_file = "boards_and_scores.json"
            self.save_file = "boards_and_scores.json"

    def run_games(self):
        for i in range(self.games_number):
            if (i + 1) % 1000 == 0 or i == 0:
                print(f"Game {i + 1}/{self.games_number}")

            game = FourInASquareGame(self.play_mode, load_json_file=self.load_file, save_json_file=self.save_file)
            game.play()
            
            result = game.check_win()
            if result in self.stats_dict:
                self.stats_dict[result] += 1
            
            game.save_game_to_dict()

    def print_tournament_result(self):
        print(f"\nResults for {self.games_number} games ({self.play_mode} mode):")
        print(f"Red wins: {self.stats_dict['Red wins']} ({self.stats_dict['Red wins'] / self.games_number * 100:.1f}%)")
        print(f"White wins: {self.stats_dict['White wins']} ({self.stats_dict['White wins'] / self.games_number * 100:.1f}%)")
        print(f"Draws: {self.stats_dict['Draw']} ({self.stats_dict['Draw'] / self.games_number * 100:.1f}%)")
        
        try:
            with open(self.save_file, "r") as f:
                boards_and_scores = json.load(f)
            print(f"\nTotal board states in {self.save_file}: {len(boards_and_scores)}")
        except FileNotFoundError:
            print(f"\nNo board states saved yet in {self.save_file}.")


if __name__ == "__main__":
    tournament = Tournament()
    tournament.run_games()
    tournament.print_tournament_result()




