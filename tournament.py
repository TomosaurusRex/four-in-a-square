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

    def run_games(self):
        for i in range(self.games_number):
            if (i + 1) % 1000 == 0 or i == 0:
                print(f"Game {i + 1}/{self.games_number}")

            game = FourInASquareGame(self.play_mode)
            game.play()
            
            result = game.check_win()
            if result in self.stats_dict:
                self.stats_dict[result] += 1
            
            # Save the game boards to the dictionary and persist to JSON
            game.save_game_to_dict()

    def print_tournament_result(self):
        print(f"\nResults for {self.games_number} games:")
        print(f"Red wins: {self.stats_dict['Red wins']} ({self.stats_dict['Red wins'] / self.games_number * 100:.1f}%)")
        print(f"White wins: {self.stats_dict['White wins']} ({self.stats_dict['White wins'] / self.games_number * 100:.1f}%)")
        print(f"Draws: {self.stats_dict['Draw']} ({self.stats_dict['Draw'] / self.games_number * 100:.1f}%)")
        
        # Load the boards_and_scores to show total learned states
        try:
            with open("boards_and_scores.json", "r") as f:
                boards_and_scores = json.load(f)
            print(f"\nTotal board states learned: {len(boards_and_scores)}")
        except FileNotFoundError:
            print("\nNo board states saved yet.")


if __name__ == "__main__":
    tournament = Tournament()
    tournament.run_games()
    tournament.print_tournament_result()


