import numpy as np
import random
import json
import copy
import os


class FourInASquareGame:
    def __init__(self, play_mode="RANDOM", load_json_file="boards_and_scores.json", save_json_file=None):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.play_mode = play_mode
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]
        self.load_json_file = load_json_file
        self.save_json_file = save_json_file if save_json_file else load_json_file

        # Load from the specified file for learning
        if os.path.exists(self.load_json_file):
            with open(self.load_json_file, "r") as f:
                self.boards_and_scores = json.load(f)
        else:
            self.boards_and_scores = {}
        

    def score_boards(self):
        num_boards = len(self.game_boards)
        boards = list(self.game_boards.keys())

        if self.check_win() == "White wins":
            outcome = 0
        elif self.check_win() == "Red wins":
            outcome = 1
        else:
            outcome = 0.5

        for i, board in enumerate(boards):
            decay = 0.96 ** (num_boards - i - 1)
            self.game_boards[board] = outcome * decay


    def save_game_to_dict(self):
        # First score the boards from this game
        self.score_boards()
        
        # Load existing save file data (might be different from load file)
        save_data = {}
        if os.path.exists(self.save_json_file):
            with open(self.save_json_file, "r") as f:
                save_data = json.load(f)
        
        # Add scored boards to save data with running averages
        for key, value in self.game_boards.items():
            if key in save_data:
                num_of_appearances = save_data[key][0]
                num_of_appearances += 1
                avg_score = ((save_data[key][1] * (num_of_appearances - 1)) + value) / num_of_appearances
                save_data[key] = (num_of_appearances, avg_score)
            else:
                save_data[key] = (1, value)
        
        # Save to the save JSON file
        with open(self.save_json_file, "w") as f:
            json.dump(save_data, f)


    @staticmethod
    def board_to_string(board_state):
        board_state_string = ""
        for sub_board in board_state:
            if sub_board == []:
                board_state_string += "    "
            else:
                for cell in sub_board:
                    board_state_string += "1" if cell == 1 else "2" if cell == 2 else "0"
        return board_state_string
    

    def refresh_sub_board_spots(self, source_idx=None, destination_idx=None):
        self.possible_sub_board_spots = [0] * 9
        self.possible_sub_board_spots[source_idx] = 2

        board_3x3 = np.array(self.possible_sub_board_spots).reshape(3, 3)

        positions = np.where(board_3x3 == 2)
        
        if len(positions[0]) > 0:
            # Extract the row and column of the tile with value 2
            source_row = positions[0][0]
            source_col = positions[1][0]
            
            # Set tiles above, below, left, and right to 1 (no diagonals)
            # Check tile above
            if source_row - 1 >= 0:
                board_3x3[source_row - 1, source_col] = 1
            
            # Check tile below
            if source_row + 1 < 3:
                board_3x3[source_row + 1, source_col] = 1
            
            # Check tile to the left
            if source_col - 1 >= 0:
                board_3x3[source_row, source_col - 1] = 1
            
            # Check tile to the right
            if source_col + 1 < 3:
                board_3x3[source_row, source_col + 1] = 1

        self.possible_sub_board_spots = board_3x3.flatten().tolist()
        self.possible_sub_board_spots[destination_idx] = 0
        

    def play(self):
        player_turn = True
        while any(spot != [] for spot in self.empty_spots):

            if player_turn:
                if self.play_mode == "RANDOM":
                    self.perform_random_agent_move()
                else:
                    self.perform_greedy_agent_move()
            else:
                self.perform_random_rival_move()

            self.game_boards[FourInASquareGame.board_to_string(self.board_state)] = 0

            result = self.check_win()

            if result != "Ongoing":
                self.save_game_to_dict()
                break

            player_turn = not player_turn


    def perform_greedy_agent_move(self):
        if random.random() > 0.9:
            self.perform_random_agent_move()
        else:
            highest_score = -1
            best_move = None
            best_sub_board_to_move = None

            for i in range(9):
                for spot in self.empty_spots[i]:
                    possible_move = copy.deepcopy(self.board_state)
                    possible_move[i][spot] = 1

                    for j in range(9):
                        if self.possible_sub_board_spots[j] == 1:
                            empty_sub_board_spot = self.possible_sub_board_spots.index(2)
                            possible_sub_board_move = copy.deepcopy(possible_move)

                            possible_sub_board_move[empty_sub_board_spot] = copy.deepcopy(possible_sub_board_move[j])
                            possible_sub_board_move[j] = []

                            possible_board_state_string = FourInASquareGame.board_to_string(possible_sub_board_move)

                            if possible_board_state_string in self.boards_and_scores:
                                score = self.boards_and_scores[possible_board_state_string][1]
                            else:
                                score = -1

                            if score > highest_score:
                                highest_score = score
                                best_move = (i, spot)
                                best_sub_board_to_move = j

            if best_move is None and best_sub_board_to_move is None:
                self.perform_random_agent_move()
                
            else:
                empty_sub_board_spot = self.possible_sub_board_spots.index(2)
                self.board_state[best_move[0]][best_move[1]] = 1
                self.empty_spots[best_move[0]].remove(best_move[1])
                self.board_state[empty_sub_board_spot] = copy.deepcopy(self.board_state[best_sub_board_to_move])
                self.empty_spots[empty_sub_board_spot] = copy.deepcopy(self.empty_spots[best_sub_board_to_move])
                self.board_state[best_sub_board_to_move] = []
                self.empty_spots[best_sub_board_to_move] = []
                self.refresh_sub_board_spots(best_sub_board_to_move, empty_sub_board_spot)


    def reset_game(self):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]


    def is_valid_move(self, sub_board, spot):
        if self.board_state[sub_board][spot] == 0:
            return True
        return False

    
    def is_valid_sub_board_move(self, source_idx, destination_idx):
        if self.possible_sub_board_spots[destination_idx] == 2 and self.possible_sub_board_spots[source_idx] == 1:
            return True
        return False
        

    def make_human_move(self, source_idx, destination_idx, sub_board, spot):
        if self.is_valid_move(sub_board, spot) and self.is_valid_sub_board_move(source_idx, destination_idx):
            self.board_state[sub_board][spot] = 1
            self.empty_spots[sub_board].remove(spot)

            self.board_state[destination_idx] = copy.deepcopy(self.board_state[source_idx])
            self.empty_spots[destination_idx] = copy.deepcopy(self.empty_spots[source_idx])
            self.board_state[source_idx] = []
            self.empty_spots[source_idx] = []
            self.refresh_sub_board_spots(source_idx, destination_idx)
            return True
        return False


    def make_random_move(self, player_value):
        """Helper method to make a random move for any player."""
        non_empty_indices = [i for i, sub_board in enumerate(self.empty_spots) if sub_board != []]
        place_sub_board_idx = random.choice(non_empty_indices)
        random_spot = random.choice(self.empty_spots[place_sub_board_idx])

        self.board_state[place_sub_board_idx][random_spot] = player_value
        self.empty_spots[place_sub_board_idx].remove(random_spot)

        available_sub_board_indices = [i for i, val in enumerate(self.possible_sub_board_spots) if val == 1]
        move_sub_board_idx = random.choice(available_sub_board_indices)

        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        self.board_state[empty_sub_board_spot] = copy.deepcopy(self.board_state[move_sub_board_idx])
        self.empty_spots[empty_sub_board_spot] = copy.deepcopy(self.empty_spots[move_sub_board_idx])
        self.board_state[move_sub_board_idx] = []
        self.empty_spots[move_sub_board_idx] = []
        self.refresh_sub_board_spots(move_sub_board_idx, empty_sub_board_spot)

    def perform_random_rival_move(self):
        self.make_random_move(2)

    def perform_random_agent_move(self):
        self.make_random_move(1)

    def check_win(self):
        b = self.board_state

        # Convert board value to text
        def player_to_text(val):
            return "Red" if val == 1 else "White"
        
        # Helper function to get value at a position in the full 6x6 grid
        def get_position(global_row, global_col):
            # Each sub-board is 2x2, arranged in a 3x3 grid of sub-boards
            sub_board_row = global_row // 2  # Which row of sub-boards (0, 1, or 2)
            sub_board_col = global_col // 2  # Which column of sub-boards (0, 1, or 2)
            sub_board_idx = sub_board_row * 3 + sub_board_col
            
            # Check if this sub-board is empty
            if b[sub_board_idx] == []:
                return 0  # Empty position
            
            # Position within the 2x2 sub-board
            pos_row = global_row % 2
            pos_col = global_col % 2
            pos_idx = pos_row * 2 + pos_col
            
            return b[sub_board_idx][pos_idx]
        
        # Check all possible 2x2 squares in the 6x6 grid
        # There are 5x5 = 25 possible 2x2 squares
        for row in range(5):
            for col in range(5):
                # Get the 2x2 square starting at (row, col)
                top_left = get_position(row, col)
                top_right = get_position(row, col + 1)
                bottom_left = get_position(row + 1, col)
                bottom_right = get_position(row + 1, col + 1)
                
                # Check if all four positions have the same non-zero value
                if (top_left == top_right == bottom_left == bottom_right != 0):
                    return f"{player_to_text(top_left)} wins"

        # Draw? (no empty spots in any non-empty sub-board)
        if not any(0 in sub_board for sub_board in b if sub_board != []):
            return "Draw"

        # Still playing
        return "Ongoing"


    def print_board(self):
        # ANSI color codes
        RED = '\033[91m'
        WHITE = '\033[97m'
        GREY = '\033[90m'
        RESET = '\033[0m'
        
        # Helper function to get cell symbol with color
        def get_cell_symbol(value):
            if value == 1:
                return f"{RED}●{RESET}"
            elif value == 2:
                return f"{WHITE}●{RESET}"
            else:
                return "·"
        
        # Helper function to print a sub-board or empty space
        def get_sub_board_display(sub_board_idx):
            sub_board = self.board_state[sub_board_idx]
            if sub_board == []:
                # Empty sub-board - display as grey
                return [
                    f"   ",
                    f"   "
                ]
            else:
                # Regular sub-board with cells
                return [
                    f"{get_cell_symbol(sub_board[0])} {get_cell_symbol(sub_board[1])}",
                    f"{get_cell_symbol(sub_board[2])} {get_cell_symbol(sub_board[3])}"
                ]
        
        print("\n" + "="*15)
        
        # Print the 3x3 grid of sub-boards
        for row in range(3):
            # Each sub-board has 2 rows
            for sub_row in range(2):
                line = ""
                for col in range(3):
                    sub_board_idx = row * 3 + col
                    display = get_sub_board_display(sub_board_idx)
                    line += display[sub_row]
                    if col < 2:
                        line += " │ "
                print(line)
            
            # Print separator between rows of sub-boards
            if row < 2:
                print("─"*4 + "┼" + "─"*5 + "┼" + "─"*4)
        
        print("="*15 + "\n")

    def print_game_result(self):
        result = self.check_win()
        RED = '\033[91m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
        
        if result == "Red wins":
            print(f"{RED}🎉 Red wins! 🎉{RESET}")
        elif result == "White wins":
            print(f"{WHITE}🎉 White wins! 🎉{RESET}")
        elif result == "Draw":
            print("🤝 It's a draw! 🤝")
        else:
            print(f"Game status: {result}")


if __name__ == "__main__":
    game = FourInASquareGame("RANDOM")
    game.play()
    #game.print_board()
    #game.print_game_result()