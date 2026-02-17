import numpy as np
import random
import json
import copy
import os


class GameModel:
    """Model for Four In A Square game - handles game state and logic"""
    
    # Class-level dictionaries for scoring and saving
    greedy_boards = {}  # Loaded from greedy file for heuristic agent
    new_boards = {}  # Only new boards from this session
    
    def __init__(self, greedy_json_file="board_dicts/greedy_boards_and_scores.json"):
        """Initialize game model for player vs heuristic AI."""
        self.greedy_json_file = greedy_json_file
        self.game_boards = {}  # Track boards played in current game

        self.total_greedy_moves = 0
        self.random_fallback_moves = 0

        # Ensure board_dicts directory exists
        os.makedirs("board_dicts", exist_ok=True)

        # Load greedy data for heuristic agent (one time only)
        if not GameModel.greedy_boards and os.path.exists(self.greedy_json_file):
            with open(self.greedy_json_file, "r") as f:
                GameModel.greedy_boards = json.load(f)
                print(f"Loaded {len(GameModel.greedy_boards)} boards from {self.greedy_json_file}")
        elif not GameModel.greedy_boards:
            print(f"Warning: {self.greedy_json_file} not found. Heuristic agent will play randomly.")

        # Game state
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], 
                           [0, 0, 0, 0], [], [0, 0, 0, 0], 
                           [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], 
                           [0, 1, 2, 3], [], [0, 1, 2, 3], 
                           [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]
        self.current_player = 1  # 1 = Red (AI), 2 = White (Player)
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], 
                           [0, 0, 0, 0], [], [0, 0, 0, 0], 
                           [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], 
                           [0, 1, 2, 3], [], [0, 1, 2, 3], 
                           [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]
        self.current_player = 1  # 1 = Red (AI), 2 = White (Player)
        self.game_boards = {}  # Clear game board history
        
    def is_valid_move(self, sub_board_idx, spot_idx):
        """Check if placing a piece at this position is valid"""
        if self.board_state[sub_board_idx] == []:
            return False
        if self.board_state[sub_board_idx][spot_idx] == 0:
            return True
        return False
    
    def is_valid_sub_board_move(self, source_idx, destination_idx):
        """Check if moving a sub-board is valid"""
        if self.possible_sub_board_spots[destination_idx] == 2 and self.possible_sub_board_spots[source_idx] == 1:
            return True
        return False
    
    def execute_move(self, sub_board_idx, spot_idx, source_idx, player_value=None, switch_player=False):
        """Execute a move: place piece and move sub-board.
        
        Args:
            sub_board_idx: Index of sub-board to place piece
            spot_idx: Index within sub-board (0-3)
            source_idx: Index of sub-board to move
            player_value: Player value (1 or 2). If None, uses current_player
            switch_player: Whether to switch current_player after move
        """
        if player_value is None:
            player_value = self.current_player
        
        # Find destination (empty spot)
        destination_idx = self.possible_sub_board_spots.index(2)
        
        # Place the piece
        self.board_state[sub_board_idx][spot_idx] = player_value
        self.empty_spots[sub_board_idx].remove(spot_idx)
        
        # Move the sub-board
        self.board_state[destination_idx] = copy.deepcopy(self.board_state[source_idx])
        self.empty_spots[destination_idx] = copy.deepcopy(self.empty_spots[source_idx])
        self.board_state[source_idx] = []
        self.empty_spots[source_idx] = []
        
        # Update possible sub-board spots
        self.refresh_sub_board_spots(source_idx, destination_idx)
        
        # Track board state for learning (only for AI moves)
        if player_value == 1:  # Only track AI (Red) moves
            self.game_boards[GameModel.board_to_string(self.board_state)] = 0
        
        # Switch player if requested
        if switch_player:
            self.current_player = 3 - self.current_player
    
    def make_move(self, sub_board_idx, spot_idx, source_idx, destination_idx):
        """Execute a move with validation: place piece and move sub-board"""
        if not self.is_valid_move(sub_board_idx, spot_idx):
            return False
        if not self.is_valid_sub_board_move(source_idx, destination_idx):
            return False
        
        # Execute the move and switch player
        self.execute_move(sub_board_idx, spot_idx, source_idx, switch_player=True)
        return True
    
    def refresh_sub_board_spots(self, source_idx, destination_idx):
        """Update which sub-boards can be selected for moving"""
        self.possible_sub_board_spots = [0] * 9
        self.possible_sub_board_spots[source_idx] = 2

        board_3x3 = np.array(self.possible_sub_board_spots).reshape(3, 3)
        positions = np.where(board_3x3 == 2)
        
        if len(positions[0]) > 0:
            source_row = positions[0][0]
            source_col = positions[1][0]
            
            # Set adjacent tiles (no diagonals)
            if source_row - 1 >= 0:
                board_3x3[source_row - 1, source_col] = 1
            if source_row + 1 < 3:
                board_3x3[source_row + 1, source_col] = 1
            if source_col - 1 >= 0:
                board_3x3[source_row, source_col - 1] = 1
            if source_col + 1 < 3:
                board_3x3[source_row, source_col + 1] = 1

        self.possible_sub_board_spots = board_3x3.flatten().tolist()
        self.possible_sub_board_spots[destination_idx] = 0
    
    def check_win(self):
        """Check game state: 'Red wins', 'White wins', 'Draw', or 'Ongoing'"""
        board_6x6 = GameModel.board_to_6x6(self.board_state)
        
        red_wins = False
        white_wins = False
        
        for i in range(5):
            for j in range(5):
                # Check 2x2 block
                block = board_6x6[i:i+2, j:j+2]
                if np.all(block == 1):
                    red_wins = True
                elif np.all(block == 2):
                    white_wins = True
        
        # Check if both players win simultaneously (draw)
        if red_wins and white_wins:
            return "Draw"
        elif red_wins:
            return "Red wins"
        elif white_wins:
            return "White wins"
                
        if any(spot != [] for spot in self.empty_spots):
            return "Ongoing"
        
        return "Draw"
    
    def get_board_state(self):
        """Return current board state for display"""
        return GameModel.board_to_string(self.board_state)
    
    def get_current_player(self):
        """Return current player (1 or 2)"""
        return self.current_player

    def score_boards(self):
        """Score all boards from the current game based on outcome."""
        num_boards = len(self.game_boards)
        boards = list(self.game_boards.keys())

        if self.check_win() == "White wins":
            outcome = 0  # Bad for AI (Red)
        elif self.check_win() == "Red wins":
            outcome = 1  # Good for AI (Red)
        else:
            outcome = 0.5  # Draw

        for i, board in enumerate(boards):
            decay = 0.96 ** (num_boards - i - 1)
            self.game_boards[board] = outcome * decay
    
    def save_game_to_dict(self):
        """Score and save current game boards to the class-level new_boards dictionary."""
        self.score_boards()
        
        # Update new_boards dictionary (session only)
        for key, value in self.game_boards.items():
            if key in GameModel.new_boards:
                num, avg = GameModel.new_boards[key]
                new_avg = ((avg * num) + value) / (num + 1)
                GameModel.new_boards[key] = (num + 1, new_avg)
            else:
                GameModel.new_boards[key] = (1, value)
    
    @staticmethod
    def save_all_to_file(filename):
        """Save all new boards from this session to file, merging with existing data."""
        # Ensure board_dicts directory exists
        os.makedirs("board_dicts", exist_ok=True)
        
        # Load existing save file
        save_data = {}
        if os.path.exists(filename):
            with open(filename, "r") as f:
                save_data = json.load(f)
        
        # Merge new boards with existing save data
        for key, value in GameModel.new_boards.items():
            if key in save_data:
                num, avg = save_data[key]
                new_num, new_avg = value
                merged_avg = ((avg * num) + (new_avg * new_num)) / (num + new_num)
                save_data[key] = (num + new_num, merged_avg)
            else:
                save_data[key] = value
        
        with open(filename, "w") as f:
            json.dump(save_data, f)
        
        print(f"Saved {len(GameModel.new_boards)} new boards to {filename}")

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
    
    def find_winning_move(self):
        """Find a move that wins the game for player 1 (AI)."""
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
                        
                        board_6x6 = GameModel.board_to_6x6(possible_board)
                        
                        for row in range(5):
                            for col in range(5):
                                block = board_6x6[row:row+2, col:col+2]
                                if np.all(block == 1):
                                    return (i, spot, j)
        return None
    
    def is_move_safe(self, move):
        """Check if a move gives the opponent an immediate winning opportunity.
        
        Returns True if the move is safe (doesn't give opponent a win).
        Returns False if the move allows opponent to win on their next turn.
        """
        our_i, our_spot, our_j = move
        
        # Simulate OUR move
        our_move = copy.deepcopy(self.board_state)
        our_move[our_i][our_spot] = 1
        
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        our_board = copy.deepcopy(our_move)
        our_board[empty_sub_board_spot] = copy.deepcopy(our_board[our_j])
        our_board[our_j] = []
        
        # Calculate new empty spots after our move
        new_empty_spots = [list(spots) for spots in self.empty_spots]
        new_empty_spots[our_i] = [s for s in new_empty_spots[our_i] if s != our_spot]
        new_empty_spots[empty_sub_board_spot] = copy.deepcopy(new_empty_spots[our_j])
        new_empty_spots[our_j] = []
        
        # Calculate new possible sub board spots after our move
        new_possible_spots = [0] * 9
        new_possible_spots[our_j] = 2
        board_3x3 = np.array(new_possible_spots).reshape(3, 3)
        positions = np.where(board_3x3 == 2)
        
        if len(positions[0]) > 0:
            source_row = positions[0][0]
            source_col = positions[1][0]
            if source_row - 1 >= 0:
                board_3x3[source_row - 1, source_col] = 1
            if source_row + 1 < 3:
                board_3x3[source_row + 1, source_col] = 1
            if source_col - 1 >= 0:
                board_3x3[source_row, source_col - 1] = 1
            if source_col + 1 < 3:
                board_3x3[source_row, source_col + 1] = 1
        
        new_possible_spots = board_3x3.flatten().tolist()
        new_possible_spots[empty_sub_board_spot] = 0
        
        # Check if opponent can win from this state
        for opp_i in range(9):
            if our_board[opp_i] == []:
                continue
            
            for opp_spot in new_empty_spots[opp_i]:
                for opp_j in range(9):
                    if new_possible_spots[opp_j] != 1:
                        continue
                    
                    opponent_response = copy.deepcopy(our_board)
                    opponent_response[opp_i][opp_spot] = 2
                    
                    opp_empty_spot = new_possible_spots.index(2)
                    opponent_final = copy.deepcopy(opponent_response)
                    opponent_final[opp_empty_spot] = copy.deepcopy(opponent_final[opp_j])
                    opponent_final[opp_j] = []
                    
                    board_6x6_opp = GameModel.board_to_6x6(opponent_final)
                    
                    for row in range(5):
                        for col in range(5):
                            block = board_6x6_opp[row:row+2, col:col+2]
                            if np.all(block == 2):
                                return False  # Move is unsafe
        
        return True  # Move is safe

    def perform_heuristic_agent_move(self):
        """Make a move using heuristics: win > safe greedy > safe random > any move."""
        # Priority 1: Find a winning move
        winning_move = self.find_winning_move()
        if winning_move:
            self.execute_move(*winning_move, player_value=1)
            return
        
        # Priority 2: Try greedy move if it's safe
        best_move = self.get_greedy_move()
        if best_move and self.is_move_safe(best_move):
            self.execute_move(*best_move, player_value=1)
            return
        
        # Priority 3: Try random moves until we find a safe one
        # Collect all possible moves
        all_possible_moves = []
        for i in range(9):
            if self.board_state[i] == []:
                continue
            for spot in self.empty_spots[i]:
                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        all_possible_moves.append((i, spot, j))
        
        # Shuffle and try to find a safe random move
        random.shuffle(all_possible_moves)
        for move in all_possible_moves:
            if self.is_move_safe(move):
                self.execute_move(*move, player_value=1)
                return
        
        # Priority 4: No safe moves exist, just execute any move
        if all_possible_moves:
            self.execute_move(*all_possible_moves[0], player_value=1)
    
    def get_greedy_move(self):
        """Get the best greedy move without executing it."""
        highest_score = -1
        best_move = None
        best_sub_board_to_move = None
        
        # Use class-level greedy_boards for heuristic mode
        score_dict = GameModel.greedy_boards

        for i in range(9):
            if self.board_state[i] == []:
                continue
            for spot in self.empty_spots[i]:
                possible_move = copy.deepcopy(self.board_state)
                possible_move[i][spot] = 1

                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
                        possible_sub_board_move = copy.deepcopy(possible_move)

                        possible_sub_board_move[empty_sub_board_spot] = copy.deepcopy(possible_sub_board_move[j])
                        possible_sub_board_move[j] = []

                        possible_board_state_string = GameModel.board_to_string(possible_sub_board_move)

                        if possible_board_state_string in score_dict:
                            score = score_dict[possible_board_state_string][1]
                        else:
                            score = -1

                        if score > highest_score:
                            highest_score = score
                            best_move = (i, spot)
                            best_sub_board_to_move = j
        
        if best_move and best_sub_board_to_move is not None:
            return (best_move[0], best_move[1], best_sub_board_to_move)
        return None