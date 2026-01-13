import numpy as np
import random
import json
import os


class FourInASquareGame:
    def __init__(self, play_mode="RANDOM"):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.play_mode = play_mode
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]

        if os.path.exists("boards_and_scores.json"):
            with open("boards_and_scores.json", "r") as f:
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
            decay = 0.9 ** (num_boards - i - 1)
            self.game_boards[board] = outcome * decay


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

        # np.where returns a tuple of arrays: (rows, cols) where condition is True
        # For a 2D array, pos[0] contains row indices, pos[1] contains column indices
        # Example: if board_3x3[1][2] == 2, then pos = ([1], [2])
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
        while self.empty_spots.__len__() > 0:

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
                self.score_boards()
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
                    possible_move = self.board_state.copy()
                    possible_move[i][spot] = 1

                    for j in range(9):
                        if self.possible_sub_board_spots[j] == 1:
                            possible_sub_board_move = possible_move.copy()
                            empty_sub_board_spot = self.possible_sub_board_spots.index(2)

                            possible_sub_board_move[empty_sub_board_spot] = self.possible_sub_board_move[j].copy()
                            possible_sub_board_move[j] = []

                            possible_board_state_string = FourInASquareGame.board_to_string(possible_sub_board_move)

                            if possible_board_state_string in self.boards_and_scores:
                                score = self.boards_and_scores[possible_board_state_string][1]
                            else:
                                score = -1

                            if score > highest_score:
                                highest_score = score
                                best_move = (i, spot)
                                best_sub_board_move = j

            if best_move is None and best_sub_board_to_move is None:
                self.perform_random_agent_move()
                
            else:
                self.board_state[best_move] = 1
                self.board_state[empty_sub_board_spot] = self.board_state[best_sub_board_to_move].copy()
                self.board_state[best_sub_board_to_move] = []
                self.empty_spots[i].remove(spot)




    def reset_game(self):
        self.board_state = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        self.empty_spots = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3]]
        self.game_boards = {}
        self.possible_sub_board_spots = [0, 1, 0, 1, 2, 1, 0, 1, 0]


    def is_valid_move(self, row, col):
        return (row, col) in self.empty_spots


    def make_human_move(self, row, col):
        if self.is_valid_move(row, col):
            self.board_state[row][col] = 1
            self.empty_spots.remove((row, col))
            return True
        else:
            return False


    def get_cell_state(self, row, col):
        return self.board_state[row][col]


    def perform_random_rival_move(self):
        pos = random.choice(self.empty_spots)
        self.board_state[pos] = 1
        self.empty_spots.remove(pos)


    def perform_random_agent_move(self):
        random_move = 



    def get_winner(self):
        if self.winner == -1:
            return "X wins"
        elif self.winner == 1:
            return "O wins"
        else:
            return "Draw"


    def check_win(self):
        b = self.board_state

        # Convert board value to text
        def player_to_text(val):
            return "X" if val == -1 else "O"

        # Check rows
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return f"{player_to_text(b[i][0])} wins"

        # Check columns
        for j in range(3):
            if b[0][j] == b[1][j] == b[2][j] != 0:
                return f"{player_to_text(b[0][j])} wins"

        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return f"{player_to_text(b[0][0])} wins"

        if b[0][2] == b[1][1] == b[2][0] != 0:
            return f"{player_to_text(b[0][2])} wins"

        # Draw? (no empty spots)
        if not any(0 in row for row in b):
            return "Draw"

        # Still playing
        return "Ongoing"


    def print_game_result(self):
        if self.winner == 1:
            print("O wins")
        elif self.winner == -1:
            print("X wins")
        else:
            print("It's a draw")


    def print_board(self):
        for i in range(3):
            row = []
            for j in range(3):
                cell = (
                    " X " if self.board_state[i][j] == -1
                    else " O " if self.board_state[i][j] == 1
                    else "   "
                )
                row.append(cell)
            print("|".join(row))
            if i < 2:
                print("---+---+---")
        print("\n")


if __name__ == "__main__":
    game = Game()
    game.play()
    game.print_board()
    game.print_game_result()