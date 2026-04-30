from model import GameModel
from view import MainMenuView, GameView, App

class GameController:
    """Controller for Four In A Square game - coordinates between model and view"""
    
    def __init__(self):
        self.model = GameModel()
        self.view = App()
        
        # Connect controller to view
        self.view.set_controller(self)
        
        # Track game phase
        self.waiting_for_piece = True  # True if waiting for piece placement, False if waiting for sub-board move
        self.piece_placement = None  # Store (sub_board_idx, spot_idx) when piece is placed
        self.game_over = False  # True once the game has ended
        self.agent_type = "HEURISTIC"  # Default agent; overridden by menu selection
        
    def start_new_game(self, agent_type=None):
        """Start a new game"""
        if agent_type is not None:
            self.agent_type = agent_type

        # Warn and fall back if NN chosen but model not loaded
        if self.agent_type == "NN" and self.model.nn_model is None:
            self.view.game.update_status(
                "⚠ NN model not found – falling back to Heuristic. "
                "Train the model first and place the .pth file in board_dicts/."
            )
            self.agent_type = "HEURISTIC"

        self.model.reset_game()
        self.waiting_for_piece = True
        self.piece_placement = None
        self.game_over = False
        
        # Show initial board state with only center black
        self.update_view()
        self.view.game.show_grid1()
        
        # AI makes the first move after a brief delay to show initial state
        self.view.window.after(500, self.ai_first_move)
    
    def _perform_ai_move(self):
        """Dispatch AI move to the correct agent based on self.agent_type."""
        if self.agent_type == "RANDOM":
            self.model._make_random_move(player_value=1)
        elif self.agent_type == "GREEDY":
            self.model.perform_greedy_agent_move()
        elif self.agent_type == "NN":
            move = self.model.get_nn_move()
            if move:
                self.model.execute_move(*move, player_value=1)
            else:
                self.model._make_random_move(player_value=1)
        else:  # Default: HEURISTIC
            self.model.perform_heuristic_agent_move()

    def ai_first_move(self):
        """Execute AI's first move"""
        agent_label = {
            "RANDOM":    "Random AI",
            "GREEDY":    "Greedy AI",
            "HEURISTIC": "Heuristic AI",
            "NN":        "Neural Net AI",
        }.get(self.agent_type, "AI")
        self.view.game.update_status(f"{agent_label} is making the first move...")
        self.view.window.update()  # Force UI update
        self._perform_ai_move()
        
        # Update view after AI move
        self.update_view()
        self.view.game.show_grid1()
        
    def handle_piece_click(self, sub_board_idx, spot_idx):
        """Handle when player clicks on a spot to place a piece"""
        if self.game_over:
            return
        if not self.waiting_for_piece:
            self.view.game.update_status("Please select a sub-board to move first!")
            return  # Not the right phase
        
        # Validate move
        if not self.model.is_valid_move(sub_board_idx, spot_idx):
            self.view.game.update_status("Invalid move! Choose an empty spot.")
            print(f"Invalid piece placement at sub-board {sub_board_idx}, spot {spot_idx}")
            return
        
        # Store the piece placement and wait for sub-board selection
        self.piece_placement = (sub_board_idx, spot_idx)
        self.waiting_for_piece = False
        
        # Update view with the pending piece shown, then switch to grid2
        self.update_view_with_pending_piece()
        self.view.game.show_grid2()
        print(f"Piece placed at sub-board {sub_board_idx}, spot {spot_idx}. Now select a sub-board to move.")
    
    def handle_sub_board_click(self, source_idx):
        """Handle when player selects sub-board to move"""
        if self.game_over:
            return
        if self.waiting_for_piece or self.piece_placement is None:
            self.view.game.update_status("Please place a piece first!")
            return  # Not the right phase
        
        # Find destination (the empty spot marked as 2)
        try:
            destination_idx = self.model.possible_sub_board_spots.index(2)
        except ValueError:
            self.view.game.update_status("Error: No empty spot found")
            print("Error: No empty spot found")
            return
        
        # Validate sub-board move
        if not self.model.is_valid_sub_board_move(source_idx, destination_idx):
            self.view.game.update_status("Invalid sub-board selection! Choose a highlighted one.")
            print(f"Invalid sub-board move from {source_idx} to {destination_idx}")
            return
        
        # Execute the player's move
        sub_board_idx, spot_idx = self.piece_placement
        self.model.execute_move(sub_board_idx, spot_idx, source_idx, player_value=2, switch_player=True)
        
        print(f"Player moved sub-board {source_idx} to {destination_idx}")
        
        # Reset for next turn
        self.piece_placement = None
        self.waiting_for_piece = True
        
        # Update view
        self.update_view()
        
        # Check for game end
        result = self.model.check_win()
        if result != "Ongoing":
            self.handle_game_end(result)
            return
        
        # AI's turn
        agent_label = {
            "RANDOM":    "Random AI",
            "GREEDY":    "Greedy AI",
            "HEURISTIC": "Heuristic AI",
            "NN":        "Neural Net AI",
        }.get(self.agent_type, "AI")
        self.view.game.update_status(f"{agent_label} is thinking...")
        self.view.window.update()  # Force UI update
        print(f"{agent_label} is thinking...")
        self._perform_ai_move()
        
        # Update view after AI move and switch back to grid1
        self.update_view()
        self.view.game.show_grid1()
        
        # Check for game end again
        result = self.model.check_win()
        if result != "Ongoing":
            self.handle_game_end(result)
    
    def update_view(self):
        """Update the game view with current model state"""
        # Update the board display
        self.view.game.update_board_display(self.model.board_state)
        
        # Update the sub-board selector display
        self.view.game.update_sub_board_display(self.model.possible_sub_board_spots, self.model.board_state)
    
    def update_view_with_pending_piece(self):
        """Update the view showing the pending piece placement before it's committed to the model"""
        import copy
        preview_board = copy.deepcopy(self.model.board_state)
        if self.piece_placement:
            sb, sp = self.piece_placement
            preview_board[sb][sp] = 2  # Player is White (2)
        
        self.view.game.update_board_display(preview_board)
        self.view.game.update_sub_board_display(self.model.possible_sub_board_spots, preview_board)
    
    def handle_game_end(self, result):
        """Handle game end (show result to player)"""
        self.game_over = True
        print(f"Game over: {result}")
        
        # Save the game boards to the new_boards dictionary
        self.model.save_game_to_dict()
        
        # Show the result to the player
        self.view.game.show_game_result(result)
    
    def get_board_state(self):
        """Get current board state from model"""
        return self.model.board_state
    
    def get_current_player(self):
        """Get current player from model"""
        return self.model.current_player
    
    def get_possible_sub_board_spots(self):
        """Get which sub-boards can be moved"""
        return self.model.possible_sub_board_spots

    def launch(self):
        self.view.run()

if __name__ == "__main__":
    controller = GameController()
    controller.launch()