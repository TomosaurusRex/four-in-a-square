import numpy as np
import random
import json
import copy
import os


class FourInASquareGame:
    # Class-level dictionaries - separate learning from saving
    learning_boards = {}  # Loaded from load_file for reference
    new_boards = {}  # Only new boards from this tournament
    
    # Statistics for greedy agent performance
    total_greedy_moves = 0
    random_fallback_moves = 0
    
    def __init__(self, play_mode="RANDOM", load_json_file="boards_and_scores.json", save_json_file=None):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.play_mode = play_mode
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]
        self.load_json_file = load_json_file
        self.save_json_file = save_json_file if save_json_file else load_json_file

        # Load learning data once
        if not FourInASquareGame.learning_boards and os.path.exists(self.load_json_file):
            with open(self.load_json_file, "r") as f:
                FourInASquareGame.learning_boards = json.load(f)
        
        self.boards_and_scores = FourInASquareGame.learning_boards
        

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
        self.score_boards()
        
        # Update new_boards dictionary (tournament session only)
        for key, value in self.game_boards.items():
            if key in FourInASquareGame.new_boards:
                num, avg = FourInASquareGame.new_boards[key]
                new_avg = ((avg * num) + value) / (num + 1)
                FourInASquareGame.new_boards[key] = (num + 1, new_avg)
            else:
                FourInASquareGame.new_boards[key] = (1, value)
    
    @staticmethod
    def save_all_to_file(filename):
        """Call this once at the end to save everything"""
        # Load existing save file
        save_data = {}
        if os.path.exists(filename):
            with open(filename, "r") as f:
                save_data = json.load(f)
        
        # Merge new boards with existing save data
        for key, value in FourInASquareGame.new_boards.items():
            if key in save_data:
                num, avg = save_data[key]
                new_num, new_avg = value
                merged_avg = ((avg * num) + (new_avg * new_num)) / (num + new_num)
                save_data[key] = (num + new_num, merged_avg)
            else:
                save_data[key] = value
        
        with open(filename, "w") as f:
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
    
    @staticmethod
    def board_to_6x6(board_state):
        """Convert 9 sub-boards (3x3 grid of 2x2 boards) into one 6x6 array."""
        board_6x6 = np.zeros((6, 6), dtype=int)
        
        for i in range(9):
            # Determine which 2x2 section of the 6x6 board this sub-board occupies
            sub_board_row = i // 3  # 0, 1, or 2
            sub_board_col = i % 3   # 0, 1, or 2
            
            # Starting position in the 6x6 array
            start_row = sub_board_row * 2
            start_col = sub_board_col * 2
            
            # Fill in the 2x2 section
            if board_state[i] != []:
                board_6x6[start_row][start_col] = board_state[i][0]
                board_6x6[start_row][start_col + 1] = board_state[i][1]
                board_6x6[start_row + 1][start_col] = board_state[i][2]
                board_6x6[start_row + 1][start_col + 1] = board_state[i][3]
            else:
                board_6x6[start_row][start_col] = 0
                board_6x6[start_row][start_col + 1] = 0
                board_6x6[start_row + 1][start_col] = 0
                board_6x6[start_row + 1][start_col + 1] = 0
        
        return board_6x6
    

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
                FourInASquareGame.random_fallback_moves += 1
                FourInASquareGame.total_greedy_moves += 1
                self.perform_random_agent_move()
                
            else:
                FourInASquareGame.total_greedy_moves += 1
                move = (best_move[0], best_move[1], best_sub_board_to_move)
                self.execute_move(move, player_value=1)


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

        available_sub_board_indices = [i for i, val in enumerate(self.possible_sub_board_spots) if val == 1]
        move_sub_board_idx = random.choice(available_sub_board_indices)
        
        move = (place_sub_board_idx, random_spot, move_sub_board_idx)
        self.execute_move(move, player_value)

    def perform_random_rival_move(self):
        self.make_random_move(2)

    def perform_random_agent_move(self):
        self.make_random_move(1)

    def find_winning_move(self):
        """Find a move that wins the game for player 1."""
        for i in range(9):
            if self.board_state[i] == []:
                continue
                
            for spot in self.empty_spots[i]:
                possible_move = copy.deepcopy(self.board_state)
                possible_move[i][spot] = 1
                
                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
                        possible_board = copy.deepcopy(possible_move)
                        
                        possible_board[empty_sub_board_spot] = copy.deepcopy(possible_board[j])
                        possible_board[j] = []
                        
                        board_6x6 = FourInASquareGame.board_to_6x6(possible_board)
                        
                        for row in range(5):
                            for col in range(5):
                                block = board_6x6[row:row+2, col:col+2]
                                if np.all(block == 1):
                                    return (i, spot, j)
        return None
    
    def find_blocking_move(self):
        """Find a move that blocks opponent from winning."""
        for i in range(9):
            if self.board_state[i] == []:
                continue
                
            for spot in self.empty_spots[i]:
                opponent_move = copy.deepcopy(self.board_state)
                opponent_move[i][spot] = 2
                
                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
                        opponent_board = copy.deepcopy(opponent_move)
                        
                        opponent_board[empty_sub_board_spot] = copy.deepcopy(opponent_board[j])
                        opponent_board[j] = []
                        
                        board_6x6_opp = FourInASquareGame.board_to_6x6(opponent_board)
                        
                        for row in range(5):
                            for col in range(5):
                                block = board_6x6_opp[row:row+2, col:col+2]
                                if np.all(block == 2):
                                    return (i, spot, j)
        return None
    
    def execute_move(self, move, player_value=1):
        """Execute a move given as (sub_board_idx, spot_idx, sub_board_to_move)."""
        sub_board_idx, spot_idx, sub_board_to_move = move
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        
        self.board_state[sub_board_idx][spot_idx] = player_value
        self.empty_spots[sub_board_idx].remove(spot_idx)
        self.board_state[empty_sub_board_spot] = copy.deepcopy(self.board_state[sub_board_to_move])
        self.empty_spots[empty_sub_board_spot] = copy.deepcopy(self.empty_spots[sub_board_to_move])
        self.board_state[sub_board_to_move] = []
        self.empty_spots[sub_board_to_move] = []
        self.refresh_sub_board_spots(sub_board_to_move, empty_sub_board_spot)

    def perform_heuristic_agent_move(self):
        """Make a move using heuristics: win > block > random/greedy."""
        # Priority 1: Find a winning move
        winning_move = self.find_winning_move()
        if winning_move:
            self.execute_move(winning_move)
            return
        
        # Priority 2: Block opponent's winning move
        blocking_move = self.find_blocking_move()
        if blocking_move:
            self.execute_move(blocking_move)
            return
        
        # Priority 3: 50/50 between random and greedy
        if random.random() < 0.5:
            self.perform_random_agent_move()
        else:
            self.perform_greedy_agent_move()


    def check_win(self):
        board_6x6 = FourInASquareGame.board_to_6x6(self.board_state)
        
        for i in range(5):
            for j in range(5):
                # Check 2x2 block
                block = board_6x6[i:i+2, j:j+2]
                if np.all(block == 1):
                    return "Red wins"
                elif np.all(block == 2):
                    return "White wins"
                
        if any(spot != [] for spot in self.empty_spots):
            return "Ongoing"
        
        return "Draw"
            

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