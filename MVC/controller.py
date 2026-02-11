from model import GameModel
from view import MainMenuView, GameView, App

class GameController:
    """Controller for Four In A Square game - coordinates between model and view"""
    
    def __init__(self):
        self.model = GameModel()
        self.view = App()
        
    def start_new_game(self):
        """Start a new game"""
        pass
        
    def handle_piece_click(self, sub_board_idx, spot_idx):
        """Handle when player clicks on a spot to place a piece"""
        pass
    
    def handle_sub_board_click(self, source_idx, destination_idx):
        """Handle when player selects sub-board to move"""
        pass
    
    def update_view(self):
        """Update the game view with current model state"""
        pass
    
    def handle_game_end(self, result):
        """Handle game end (show result to player)"""
        pass
    
    def get_board_state(self):
        """Get current board state from model"""
        pass
    
    def get_current_player(self):
        """Get current player from model"""
        pass
    
    def get_possible_sub_board_spots(self):
        """Get which sub-boards can be moved"""
        pass

    def launch(self):
        self.view.run()

if __name__ == "__main__":
    controller = GameController()
    controller.launch()