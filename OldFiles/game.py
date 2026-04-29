import random
import pickle
import os


class FourInASquareGame:
    # Class-level dictionaries - separate learning from saving
    learning_boards = {}  # Loaded from load_file for reference
    greedy_boards = {}  # Loaded from greedy file for heuristic agent
    new_boards = {}  # Only new boards from this tournament
    
    # Statistics for greedy agent performance
    total_greedy_moves = 0
    random_fallback_moves = 0
    
    # Pre-computed neighbor lookup for the 3x3 sub-board grid
    NEIGHBORS = {
        0: [1, 3], 1: [0, 2, 4], 2: [1, 5],
        3: [0, 4, 6], 4: [1, 3, 5, 7], 5: [2, 4, 8],
        6: [3, 7], 7: [4, 6, 8], 8: [5, 7]
    }

    @staticmethod
    def _copy_board(board_state):
        """Lightweight board copy — avoids expensive copy.deepcopy."""
        return [list(sub) if sub else [] for sub in board_state]

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
        get = FourInASquareGame._get_cell
        for r in range(5):
            for c in range(5):
                if (get(board_state, r, c) == player and
                    get(board_state, r, c + 1) == player and
                    get(board_state, r + 1, c) == player and
                    get(board_state, r + 1, c + 1) == player):
                    return True
        return False

    def __init__(self, play_mode="RANDOM", load_file="board_dicts/boards_and_scores.pkl", save_file=None, greedy_file="board_dicts/greedy_boards_and_scores.pkl", exploration_rate=0.1):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.play_mode = play_mode
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]
        self.load_file = load_file
        self.save_file = save_file if save_file else load_file
        self.greedy_file = greedy_file
        self.exploration_rate = exploration_rate

        # Ensure board_dicts directory exists
        os.makedirs("board_dicts", exist_ok=True)

        # Load learning data once
        if not FourInASquareGame.learning_boards and os.path.exists(self.load_file):
            with open(self.load_file, "rb") as f:
                FourInASquareGame.learning_boards = pickle.load(f)
        
        # Load greedy data for heuristic agent
        if not FourInASquareGame.greedy_boards and os.path.exists(self.greedy_file):
            with open(self.greedy_file, "rb") as f:
                FourInASquareGame.greedy_boards = pickle.load(f)
        
        self.boards_and_scores = FourInASquareGame.learning_boards
        

    def score_boards(self):
        num_boards = len(self.game_boards)
        boards = list(self.game_boards.keys())

        result = self.check_win()
        if result == "White wins":
            outcome = 0
        elif result == "Red wins":
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
        """Call this once at the end to save everything.
        Merges new_boards into learning_boards in memory, then writes to disk once."""
        # Ensure board_dicts directory exists
        os.makedirs("board_dicts", exist_ok=True)
        
        # Merge new boards into the in-memory dict (avoids re-reading from disk)
        save_data = FourInASquareGame.learning_boards
        for key, value in FourInASquareGame.new_boards.items():
            if key in save_data:
                num, avg = save_data[key]
                new_num, new_avg = value
                merged_avg = ((avg * num) + (new_avg * new_num)) / (num + new_num)
                save_data[key] = (num + new_num, merged_avg)
            else:
                save_data[key] = value
        
        with open(filename, "wb") as f:
            pickle.dump(save_data, f, protocol=pickle.HIGHEST_PROTOCOL)


    @staticmethod
    def board_to_string(board_state):
        parts = []
        for sub_board in board_state:
            if not sub_board:
                parts.append("    ")
            else:
                parts.extend("1" if c == 1 else "2" if c == 2 else "0" for c in sub_board)
        return ''.join(parts)
    
    @staticmethod
    def board_to_6x6(board_state):
        """Convert 9 sub-boards (3x3 grid of 2x2 boards) into one 6x6 array."""
        board_6x6 = [[0] * 6 for _ in range(6)]
        
        for i in range(9):
            if not board_state[i]:
                continue
            start_row = (i // 3) * 2
            start_col = (i % 3) * 2
            board_6x6[start_row][start_col] = board_state[i][0]
            board_6x6[start_row][start_col + 1] = board_state[i][1]
            board_6x6[start_row + 1][start_col] = board_state[i][2]
            board_6x6[start_row + 1][start_col + 1] = board_state[i][3]
        
        return board_6x6
    

    def refresh_sub_board_spots(self, source_idx=None, destination_idx=None):
        self.possible_sub_board_spots = [0] * 9
        self.possible_sub_board_spots[source_idx] = 2
        for n in FourInASquareGame.NEIGHBORS[source_idx]:
            self.possible_sub_board_spots[n] = 1
        self.possible_sub_board_spots[destination_idx] = 0
        

    def play(self):
        player_turn = True
        while any(spot != [] for spot in self.empty_spots):

            if player_turn:
                if self.play_mode == "RANDOM":
                    self.perform_random_agent_move()
                elif self.play_mode == "HEURISTIC_VS_HEURISTIC":
                    self.perform_heuristic_agent_move(exploration_rate=self.exploration_rate)
                elif self.play_mode == "HEURISTIC":
                    self.perform_heuristic_agent_move()
                else:
                    self.perform_greedy_agent_move()
            else:
                if self.play_mode == "HEURISTIC_VS_HEURISTIC":
                    self.perform_heuristic_rival_move()
                else:
                    self.perform_random_rival_move()

            self.game_boards[FourInASquareGame.board_to_string(self.board_state)] = 0

            result = self.check_win()

            if result != "Ongoing":
                self.save_game_to_dict()
                break

            player_turn = not player_turn


    def perform_greedy_agent_move(self):
        if random.random() < self.exploration_rate:
            FourInASquareGame.random_fallback_moves += 1
            FourInASquareGame.total_greedy_moves += 1
            self.perform_random_agent_move()
        else:
            best_move = self.get_greedy_move()

            if best_move is None:
                FourInASquareGame.random_fallback_moves += 1
                FourInASquareGame.total_greedy_moves += 1
                self.perform_random_agent_move()
                
            else:
                FourInASquareGame.total_greedy_moves += 1
                self.execute_move(best_move, player_value=1)


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

            self.board_state[destination_idx] = list(self.board_state[source_idx])
            self.empty_spots[destination_idx] = list(self.empty_spots[source_idx])
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

    def find_winning_move(self, player=1):
        """Find a move that wins the game for the given player."""
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        for i in range(9):
            if not self.board_state[i]:
                continue
                
            for spot in self.empty_spots[i]:
                # Mutate piece placement
                self.board_state[i][spot] = player
                
                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        # Mutate sub-board swap
                        saved_empty = self.board_state[empty_sub_board_spot]
                        self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                        saved_j = self.board_state[j]
                        self.board_state[j] = []
                        
                        if FourInASquareGame._check_player_wins(self.board_state, player):
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
    
    def is_move_safe(self, move, player=1):
        """Check if a move gives the opponent an immediate winning opportunity.
        
        Returns True if the move is safe (doesn't give opponent a win).
        Returns False if the move allows opponent to win on their next turn.
        """
        our_i, our_spot, our_j = move
        opponent = 3 - player
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        
        # Simulate our move with lightweight copy
        our_board = FourInASquareGame._copy_board(self.board_state)
        our_board[our_i][our_spot] = player
        our_board[empty_sub_board_spot] = list(our_board[our_j])
        our_board[our_j] = []
        
        # Calculate new empty spots after our move
        new_empty_spots = [list(spots) for spots in self.empty_spots]
        new_empty_spots[our_i] = [s for s in new_empty_spots[our_i] if s != our_spot]
        new_empty_spots[empty_sub_board_spot] = list(new_empty_spots[our_j])
        new_empty_spots[our_j] = []
        
        # Calculate new possible sub board spots using NEIGHBORS
        new_possible_spots = [0] * 9
        new_possible_spots[our_j] = 2
        for n in FourInASquareGame.NEIGHBORS[our_j]:
            new_possible_spots[n] = 1
        new_possible_spots[empty_sub_board_spot] = 0
        
        opp_empty_spot = new_possible_spots.index(2)

        # Check if opponent can win from this state using mutate/unmake
        for opp_i in range(9):
            if not our_board[opp_i]:
                continue
            
            for opp_spot in new_empty_spots[opp_i]:
                for opp_j in range(9):
                    if new_possible_spots[opp_j] != 1:
                        continue
                    
                    # Mutate: place opponent piece
                    saved_cell = our_board[opp_i][opp_spot]
                    our_board[opp_i][opp_spot] = opponent

                    # Mutate: sub-board swap
                    saved_opp_empty = our_board[opp_empty_spot]
                    saved_opp_j = our_board[opp_j]
                    our_board[opp_empty_spot] = list(our_board[opp_j])
                    our_board[opp_j] = []
                    
                    if FourInASquareGame._check_player_wins(our_board, opponent):
                        return False  # Move is unsafe
                    
                    # Unmake sub-board swap and piece placement
                    our_board[opp_j] = saved_opp_j
                    our_board[opp_empty_spot] = saved_opp_empty
                    our_board[opp_i][opp_spot] = saved_cell
        
        return True  # Move is safe
    
    def execute_move(self, move, player_value=1):
        """Execute a move given as (sub_board_idx, spot_idx, sub_board_to_move)."""
        sub_board_idx, spot_idx, sub_board_to_move = move
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        
        self.board_state[sub_board_idx][spot_idx] = player_value
        self.empty_spots[sub_board_idx].remove(spot_idx)
        self.board_state[empty_sub_board_spot] = list(self.board_state[sub_board_to_move])
        self.empty_spots[empty_sub_board_spot] = list(self.empty_spots[sub_board_to_move])
        self.board_state[sub_board_to_move] = []
        self.empty_spots[sub_board_to_move] = []
        self.refresh_sub_board_spots(sub_board_to_move, empty_sub_board_spot)

    @staticmethod
    def _evaluate_position(board_state, player):
        """Evaluate board position using 2x2 window scanning.
        
        Scores the board from `player`'s perspective by classifying
        every 2x2 window on the 6x6 grid.
        
        Returns (score, num_three_threats) where num_three_threats is
        how many windows have 3-of-ours + 1-empty (for fork detection).
        """
        get = FourInASquareGame._get_cell
        opponent = 3 - player
        score = 0
        three_threats = 0

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
                    score += 10000  # Win
                elif mine == 3 and empty == 1:
                    score += 400
                    three_threats += 1
                elif mine == 2 and empty == 2:
                    score += 40
                elif mine == 1 and empty == 3:
                    score += 5

                # Opponent formations
                elif theirs == 3 and empty == 1:
                    score -= 500  # Must block
                elif theirs == 2 and empty == 2:
                    score -= 25

        # Fork bonus: 2+ three-threats is nearly unstoppable
        if three_threats >= 2:
            score += 600

        return score, three_threats

    def perform_heuristic_agent_move(self, player=1, exploration_rate=0.0):
        """Make a move using heuristics:
        1. Instant win → play it
        2. Score all moves via window evaluation
        3. Safety-check top candidates
        4. Play highest-scoring safe move
        """
        if random.random() < exploration_rate:
            self.make_random_move(player)
            return

        # Priority 1: Find a winning move (early exit)
        winning_move = self.find_winning_move(player)
        if winning_move:
            self.execute_move(winning_move, player_value=player)
            return

        # Collect all legal moves and score them
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)
        scored_moves = []

        for i in range(9):
            if not self.board_state[i]:
                continue
            for spot in self.empty_spots[i]:
                # Mutate: place piece
                self.board_state[i][spot] = player

                for j in range(9):
                    if self.possible_sub_board_spots[j] != 1:
                        continue

                    # Mutate: sub-board swap
                    saved_empty = self.board_state[empty_sub_board_spot]
                    self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                    saved_j = self.board_state[j]
                    self.board_state[j] = []

                    # Score the resulting position
                    score, _ = FourInASquareGame._evaluate_position(self.board_state, player)

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
            if self.is_move_safe((i, spot, j), player):
                self.execute_move((i, spot, j), player_value=player)
                return

        # If none of the top moves are safe, try the rest
        for score, i, spot, j in scored_moves[TOP_N:]:
            if self.is_move_safe((i, spot, j), player):
                self.execute_move((i, spot, j), player_value=player)
                return

        # No safe moves exist — play the highest-scored move anyway
        _, i, spot, j = scored_moves[0]
        self.execute_move((i, spot, j), player_value=player)

    def perform_heuristic_rival_move(self):
        self.perform_heuristic_agent_move(player=2, exploration_rate=self.exploration_rate)
    
    def get_greedy_move(self):
        """Get the best greedy move without executing it (used by GREEDY mode only)."""
        highest_score = -1
        best_move = None
        
        score_dict = self.boards_and_scores
        empty_sub_board_spot = self.possible_sub_board_spots.index(2)

        for i in range(9):
            for spot in self.empty_spots[i]:
                # Mutate piece placement
                self.board_state[i][spot] = 1

                for j in range(9):
                    if self.possible_sub_board_spots[j] == 1:
                        # Mutate sub-board swap
                        saved_empty = self.board_state[empty_sub_board_spot]
                        self.board_state[empty_sub_board_spot] = list(self.board_state[j])
                        saved_j = self.board_state[j]
                        self.board_state[j] = []

                        key = FourInASquareGame.board_to_string(self.board_state)

                        if key in score_dict:
                            score = score_dict[key][1]
                            if score > highest_score:
                                highest_score = score
                                best_move = (i, spot, j)
                                if score >= 1.0:  # Early termination on perfect score
                                    self.board_state[j] = saved_j
                                    self.board_state[empty_sub_board_spot] = saved_empty
                                    self.board_state[i][spot] = 0
                                    return best_move

                        # Unmake sub-board swap
                        self.board_state[j] = saved_j
                        self.board_state[empty_sub_board_spot] = saved_empty

                # Unmake piece placement
                self.board_state[i][spot] = 0

        return best_move


    def check_win(self):
        red_wins = FourInASquareGame._check_player_wins(self.board_state, 1)
        white_wins = FourInASquareGame._check_player_wins(self.board_state, 2)
        
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