import random
import pickle
import os
import torch
import torch.nn as nn


def _encode_board_string(board_str):
    """Encode a 36-char board string into a 144-float one-hot vector.
    Each character maps to a 4-element one-hot:
      '0' -> [1,0,0,0]  (empty cell)
      '1' -> [0,1,0,0]  (Red / AI piece)
      '2' -> [0,0,1,0]  (White / player piece)
      ' ' -> [0,0,0,1]  (missing sub-board slot)
    """
    vec = []
    for char in board_str:
        if char == ' ':
            vec.extend([0.0, 0.0, 0.0, 1.0])
        else:
            v = int(char)
            one_hot = [0.0, 0.0, 0.0, 0.0]
            one_hot[v] = 1.0
            vec.extend(one_hot)
    return vec


class FourInASquareNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(144, 256)
        self.dropout1 = nn.Dropout(0.2)
        self.layer2 = nn.Linear(256, 128)
        self.dropout2 = nn.Dropout(0.2)
        self.layer3 = nn.Linear(128, 64)
        self.output = nn.Linear(64, 1)
        self.activation = nn.LeakyReLU(0.01)

    def forward(self, x):
        x = self.activation(self.layer1(x))
        x = self.dropout1(x)
        x = self.activation(self.layer2(x))
        x = self.dropout2(x)
        x = self.activation(self.layer3(x))
        x = torch.sigmoid(self.output(x))
        return x


class GameModel:
    """Model for Four In A Square game - handles game state and logic"""
    
    # Class-level dictionaries for scoring and saving
    new_boards = {}       # Only new boards from this session
    learning_boards = {}  # Loaded from pkl file for greedy lookup
    
    # Pre-computed neighbor lookup for the 3x3 sub-board grid
    NEIGHBORS = {
        0: [1, 3], 1: [0, 2, 4], 2: [1, 5],
        3: [0, 4, 6], 4: [1, 3, 5, 7], 5: [2, 4, 8],
        6: [3, 7], 7: [4, 6, 8], 8: [5, 7]
    }

    @staticmethod
    def _get_cell(board_state, row, col):
        """Get cell value at (row, col) in the 6x6 representation."""
        sb = (row // 2) * 3 + (col // 2)
        if not board_state[sb]:
            return 0
        return board_state[sb][(row % 2) * 2 + (col % 2)]

    @staticmethod
    def _check_player_wins(board_state, player):
        """Check if player has a 2x2 block anywhere on the board."""
        get = GameModel._get_cell
        for r in range(5):
            for c in range(5):
                if (get(board_state, r, c) == player and
                    get(board_state, r, c + 1) == player and
                    get(board_state, r + 1, c) == player and
                    get(board_state, r + 1, c + 1) == player):
                    return True
        return False
    
    def __init__(self, load_file="board_dicts/heuristic_boards_and_scores.pkl"):
        """Initialize game model for player vs heuristic AI."""
        self.game_boards = {}  # Track boards played in current game
        self.load_file = load_file
        self.save_file = load_file

        # Ensure board_dicts directory exists
        os.makedirs("board_dicts", exist_ok=True)

        # Load learning data once (class-level, shared across instances)
        if not GameModel.learning_boards and os.path.exists(self.load_file):
            with open(self.load_file, "rb") as f:
                GameModel.learning_boards = pickle.load(f)

        # Load trained NN model if available
        nn_path = "board_dicts/four_in_a_square_model.pth"
        self.nn_model = None
        if os.path.exists(nn_path):
            self.nn_model = FourInASquareNet()
            self.nn_model.load_state_dict(torch.load(nn_path, map_location="cpu", weights_only=True))
            self.nn_model.eval()

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
        self.board_state[destination_idx] = list(self.board_state[source_idx])
        self.empty_spots[destination_idx] = list(self.empty_spots[source_idx])
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
        for n in GameModel.NEIGHBORS[source_idx]:
            self.possible_sub_board_spots[n] = 1
        self.possible_sub_board_spots[destination_idx] = 0
    
    def check_win(self):
        """Check game state: 'Red wins', 'White wins', 'Draw', or 'Ongoing'"""
        red_wins = GameModel._check_player_wins(self.board_state, 1)
        white_wins = GameModel._check_player_wins(self.board_state, 2)
        
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

        result = self.check_win()
        if result == "White wins":
            outcome = 0  # Bad for AI (Red)
        elif result == "Red wins":
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
        """Save all new boards from this session to pkl file, merging with existing data."""
        os.makedirs("board_dicts", exist_ok=True)

        # Merge new_boards into the already-loaded in-memory dict
        save_data = GameModel.learning_boards
        for key, value in GameModel.new_boards.items():
            if key in save_data:
                num, avg = save_data[key]
                new_num, new_avg = value
                merged_avg = ((avg * num) + (new_avg * new_num)) / (num + new_num)
                save_data[key] = (num + new_num, merged_avg)
            else:
                save_data[key] = value

        with open(filename, "wb") as f:
            pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)

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
    
    def get_greedy_move(self):
        """Look up the best move using pre-computed scores from the pkl file.
        Returns (sub_board_idx, spot_idx, source_idx) or None if no known board found."""
        highest_score = -1
        best_move = None
        score_dict = GameModel.learning_boards
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        for i in range(9):
            if not self.board_state[i]:
                continue
            for spot in self.empty_spots[i]:
                self.board_state[i][spot] = 1

                for j in range(9):
                    if self.possible_sub_board_spots[j] != 1:
                        continue

                    saved_empty = self.board_state[empty_sub_board_spot]
                    self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                    saved_j = self.board_state[j]
                    self.board_state[j] = []

                    key = GameModel.board_to_string(self.board_state)
                    if key in score_dict:
                        score = score_dict[key][1]
                        if score > highest_score:
                            highest_score = score
                            best_move = (i, spot, j)
                            if score >= 1.0:  # Perfect score — stop early
                                self.board_state[j] = saved_j
                                self.board_state[empty_sub_board_spot] = saved_empty
                                self.board_state[i][spot] = 0
                                return best_move

                    self.board_state[j] = saved_j
                    self.board_state[empty_sub_board_spot] = saved_empty

                self.board_state[i][spot] = 0

        return best_move

    def get_nn_move(self):
        """Score every legal move with the trained NN and return the best one.
        Returns (sub_board_idx, spot_idx, source_idx) or None if no model loaded."""
        if self.nn_model is None:
            return None

        best_score = float('-inf')
        best_move = None
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        self.nn_model.eval()
        for i in range(9):
            if not self.board_state[i]:
                continue
            # Skip the empty slot: the j-loop will overwrite board_state[i]
            # mid-iteration when i == empty_sub_board_spot, corrupting the search.
            if i == empty_sub_board_spot:
                continue
            for spot in list(self.empty_spots[i]):
                self.board_state[i][spot] = 1

                for j in range(9):
                    if self.possible_sub_board_spots[j] != 1:
                        continue

                    saved_empty = self.board_state[empty_sub_board_spot]
                    self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                    saved_j = self.board_state[j]
                    self.board_state[j] = []

                    vec = _encode_board_string(GameModel.board_to_string(self.board_state))
                    with torch.no_grad():
                        score = self.nn_model(
                            torch.tensor([vec], dtype=torch.float32)
                        ).item()

                    if score > best_score:
                        best_score = score
                        best_move = (i, spot, j)

                    self.board_state[j] = saved_j
                    self.board_state[empty_sub_board_spot] = saved_empty

                self.board_state[i][spot] = 0

        return best_move

    def perform_nn_agent_move(self):
        """Make a move using the trained neural network.
        Falls back to heuristic if the model is not loaded."""
        if self.nn_model is None:
            self.perform_heuristic_agent_move()
            return
        move = self.get_nn_move()
        if move:
            self.execute_move(*move, player_value=1)
        else:
            self._make_random_move(player_value=1)

    def perform_greedy_agent_move(self, exploration_rate=0.1):
        """Make a move using pre-computed pkl scores (greedy lookup).
        Falls back to random if no known board is found or on exploration."""
        if random.random() < exploration_rate or not GameModel.learning_boards:
            self._make_random_move(player_value=1)
            return

        best_move = self.get_greedy_move()
        if best_move is None:
            self._make_random_move(player_value=1)
        else:
            self.execute_move(*best_move, player_value=1)

    def _make_random_move(self, player_value):
        """Make a fully random legal move for the given player."""
        non_empty = [i for i, sub in enumerate(self.empty_spots) if sub]
        i = random.choice(non_empty)
        spot = random.choice(self.empty_spots[i])
        available = [j for j, val in enumerate(self.possible_sub_board_spots) if val == 1]
        j = random.choice(available)
        self.execute_move(i, spot, j, player_value=player_value)

    def find_winning_move(self):
        """Find a move that wins the game for player 1 (AI).
        Uses mutate/unmake for zero-copy performance."""
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        for i in range(9):
            if not self.board_state[i]:
                continue
                
            for spot in self.empty_spots[i]:
                # Mutate: place piece
                self.board_state[i][spot] = 1
                
                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        # Mutate: sub-board swap
                        saved_empty = self.board_state[empty_sub_board_spot]
                        self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                        saved_j = self.board_state[j]
                        self.board_state[j] = []
                        
                        if GameModel._check_player_wins(self.board_state, 1):
                            # Unmake before returning
                            self.board_state[j] = saved_j
                            self.board_state[empty_sub_board_spot] = saved_empty
                            self.board_state[i][spot] = 0
                            return (i, spot, j)
                        
                        # Unmake sub-board swap
                        self.board_state[j] = saved_j
                        self.board_state[empty_sub_board_spot] = saved_empty
                
                # Unmake piece placement
                self.board_state[i][spot] = 0

        return None
    
    def is_move_safe(self, move):
        """Check if a move gives the opponent an immediate winning opportunity.

        Uses full mutate/unmake on self.board_state and self.empty_spots —
        no board copies allocated.

        Returns True if the move is safe (doesn't give opponent a win).
        Returns False if the move allows opponent to win on their next turn.
        """
        our_i, our_spot, our_j = move
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        # --- Mutate: simulate our move ---
        self.board_state[our_i][our_spot] = 1
        saved_dest_board = self.board_state[empty_sub_board_spot]   # always []
        self.board_state[empty_sub_board_spot] = list(self.board_state[our_j])
        saved_our_j_board = self.board_state[our_j]
        self.board_state[our_j] = []

        saved_empty_i = self.empty_spots[our_i]
        self.empty_spots[our_i] = [s for s in saved_empty_i if s != our_spot]
        saved_empty_dest = self.empty_spots[empty_sub_board_spot]
        self.empty_spots[empty_sub_board_spot] = list(self.empty_spots[our_j])
        saved_empty_our_j = self.empty_spots[our_j]
        self.empty_spots[our_j] = []

        # Post-move opponent possibilities (our_j is now the empty slot)
        new_possible = [0] * 9
        new_possible[our_j] = 2
        for n in GameModel.NEIGHBORS[our_j]:
            new_possible[n] = 1
        new_possible[empty_sub_board_spot] = 0
        opp_new_empty = our_j  # == new_possible.index(2)

        # --- Check every opponent reply ---
        result = True
        for opp_i in range(9):
            if not self.board_state[opp_i]:
                continue
            for opp_spot in self.empty_spots[opp_i]:
                for opp_j in range(9):
                    if new_possible[opp_j] != 1:
                        continue
                    # Mutate: opponent move
                    self.board_state[opp_i][opp_spot] = 2
                    saved_opp_dest = self.board_state[opp_new_empty]
                    self.board_state[opp_new_empty] = list(self.board_state[opp_j])
                    saved_opp_j = self.board_state[opp_j]
                    self.board_state[opp_j] = []

                    if GameModel._check_player_wins(self.board_state, 2):
                        result = False

                    # Unmake: opponent move
                    self.board_state[opp_j] = saved_opp_j
                    self.board_state[opp_new_empty] = saved_opp_dest
                    self.board_state[opp_i][opp_spot] = 0  # was empty before

                    if not result:
                        break
                if not result:
                    break
            if not result:
                break

        # --- Unmake: our move ---
        self.empty_spots[our_j] = saved_empty_our_j
        self.empty_spots[empty_sub_board_spot] = saved_empty_dest
        self.empty_spots[our_i] = saved_empty_i
        self.board_state[our_j] = saved_our_j_board
        self.board_state[empty_sub_board_spot] = saved_dest_board
        self.board_state[our_i][our_spot] = 0

        return result

    @staticmethod
    def _evaluate_position(board_state, player):
        """Evaluate board position using 2x2 window scanning.
        
        Scores the board from `player`'s perspective by classifying
        every 2x2 window on the 6x6 grid.
        
        Returns (score, num_three_threats).
        """
        get = GameModel._get_cell
        opponent = 3 - player
        score = 0
        three_threats = 0
        opp_three_threats = 0

        for r in range(5):
            for c in range(5):
                tl = get(board_state, r, c)
                tr = get(board_state, r, c + 1)
                bl = get(board_state, r + 1, c)
                br = get(board_state, r + 1, c + 1)

                mine = (tl == player) + (tr == player) + (bl == player) + (br == player)
                theirs = (tl == opponent) + (tr == opponent) + (bl == opponent) + (br == opponent)
                empty = 4 - mine - theirs

                # Dead window (both colors present) — skip
                if mine > 0 and theirs > 0:
                    continue

                # Our formations
                if mine == 4:
                    score += 10000
                elif mine == 3 and empty == 1:
                    score += 400
                    three_threats += 1
                elif mine == 2 and empty == 2:
                    score += 40
                elif mine == 1 and empty == 3:
                    score += 5

                # Opponent formations
                elif theirs == 3 and empty == 1:
                    score -= 500
                    opp_three_threats += 1
                elif theirs == 2 and empty == 2:
                    score -= 25

        # Fork bonus: 2+ three-threats is nearly unstoppable
        if three_threats >= 2:
            score += 600
        # Opponent fork penalty: leaving them with 2+ three-threats is nearly losing
        if opp_three_threats >= 2:
            score -= 800

        return score, three_threats

    def perform_heuristic_agent_move(self):
        """Make a move using heuristics:
        1. Instant win -> play it
        2. Score all moves via window evaluation
        3. Safety-check top candidates
        4. Play highest-scoring safe move
        """
        # Priority 1: Find a winning move (early exit)
        winning_move = self.find_winning_move()
        if winning_move:
            self.execute_move(*winning_move, player_value=1)
            return

        # Collect all legal moves and score them
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        scored_moves = []

        for i in range(9):
            if not self.board_state[i]:
                continue
            for spot in self.empty_spots[i]:
                # Mutate: place piece
                self.board_state[i][spot] = 1

                for j in range(9):
                    if self.possible_sub_board_spots[j] != 1:
                        continue

                    # Mutate: sub-board swap
                    saved_empty = self.board_state[empty_sub_board_spot]
                    self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                    saved_j = self.board_state[j]
                    self.board_state[j] = []

                    # Score the resulting position
                    score, _ = GameModel._evaluate_position(self.board_state, 1)

                    scored_moves.append((score, i, spot, j))

                    # Unmake sub-board swap
                    self.board_state[j] = saved_j
                    self.board_state[empty_sub_board_spot] = saved_empty

                # Unmake piece placement
                self.board_state[i][spot] = 0

        if not scored_moves:
            return  # No legal moves

        # Sort descending by score
        scored_moves.sort(key=lambda x: x[0], reverse=True)

        # Safety-check top candidates (max 5) to avoid expensive full scan
        TOP_N = 5
        for score, i, spot, j in scored_moves[:TOP_N]:
            if self.is_move_safe((i, spot, j)):
                self.execute_move(i, spot, j, player_value=1)
                return

        # If none of the top moves are safe, try the rest
        for score, i, spot, j in scored_moves[TOP_N:]:
            if self.is_move_safe((i, spot, j)):
                self.execute_move(i, spot, j, player_value=1)
                return

        # No safe moves exist — play the highest-scored move anyway
        _, i, spot, j = scored_moves[0]
        self.execute_move(i, spot, j, player_value=1)