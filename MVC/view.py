import tkinter as tk
from PIL import Image, ImageTk
import os

class MainMenuView:
    def __init__(self, window, app, scale=1.0):
        self.window = window
        self.app = app
        self.scale = scale
        self.frame = tk.Frame(self.window)

        self.start_game_button = tk.Button(
            self.frame, text="Start Game",
            font=("Arial", int(14 * scale)),
            command=self.on_start_game
        )
        self.start_game_button.pack(pady=int(20 * scale))
        # TODO: Add title, buttons, etc.
        
    def on_start_game(self):
        self.app.show_game()

    def show(self):
        self.frame.pack()
        
    def hide(self):
        self.frame.pack_forget()


class GameView:
    def __init__(self, window, app, controller=None, scale=1.0):
        self.window = window
        self.app = app
        self.controller = controller
        self.scale = scale
        self.frame = tk.Frame(self.window)

        # Model state indexes - track current selections
        self.selected_sub_board_idx = None  # Which sub-board to place piece (0-8)
        self.selected_spot_idx = None       # Which spot within sub-board (0-3)
        self.selected_source_idx = None     # Which sub-board to move (0-8)
        
        # Store button references for updating
        self.grid1_buttons = {}  # {(row, col): button}
        self.grid1_sub_frames = {}  # {sub_board_idx: frame}
        self.grid2_buttons = {}  # {(row, col): button}
        self.grid2_sub_frames = {}  # {sub_board_idx: frame}
        
        self.return_menu_button = tk.Button(self.frame, text="Return to Menu", command=self.on_return_menu)
        self.return_menu_button.pack(pady=int(20 * scale))

        # Status label to show current state
        self.status_label = tk.Label(self.frame, text="Place your piece", font=("Arial", int(14 * scale)))
        self.status_label.pack(pady=int(10 * scale))

        # Container frame for both grids at the same position
        _grid_size = int(650 * scale)
        self.grid_container = tk.Frame(self.frame, width=_grid_size, height=_grid_size)
        self.grid_container.pack(pady=int(10 * scale))
        self.grid_container.pack_propagate(False)  # Don't shrink to fit content
        
        # Both grids placed in the same container
        self.grid1_frame = tk.Frame(self.grid_container)
        self.grid2_frame = tk.Frame(self.grid_container)
        
        # Place both frames at the same position
        self.grid1_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.grid2_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Store pixel as instance variable to prevent garbage collection
        self.pixel = tk.PhotoImage(width=1, height=1)

        # Create 6x6 grid for placing pieces, wrapped in 2x2 sub-board frames
        for sb_row in range(3):
            for sb_col in range(3):
                sub_board_idx = sb_row * 3 + sb_col
                sub_frame = tk.Frame(self.grid1_frame, bg="#000000", bd=2, relief=tk.FLAT)
                sub_frame.grid(row=sb_row, column=sb_col, padx=1, pady=1)
                self.grid1_sub_frames[sub_board_idx] = sub_frame
                
                for spot_row in range(2):
                    for spot_col in range(2):
                        spot_idx = spot_row * 2 + spot_col
                        row = sb_row * 2 + spot_row
                        col = sb_col * 2 + spot_col
                        
                        _btn_size = int(100 * scale)
                        if sub_board_idx == 4:
                            btn = tk.Button(sub_frame, image=self.pixel, width=_btn_size, height=_btn_size,
                                          relief=tk.SUNKEN, bg="#000000", state=tk.DISABLED)
                        else:
                            btn = tk.Button(sub_frame, image=self.pixel, width=_btn_size, height=_btn_size,
                                          relief=tk.RAISED, bg="#3a3a3a",
                                          command=lambda sb=sub_board_idx, sp=spot_idx: self.on_piece_click(sb, sp))
                        btn.grid(row=spot_row, column=spot_col)
                        self.grid1_buttons[(row, col)] = btn

        # Create 6x6 grid for selecting sub-boards to move, wrapped in 2x2 sub-board frames
        for sb_row in range(3):
            for sb_col in range(3):
                sub_board_idx = sb_row * 3 + sb_col
                sub_frame = tk.Frame(self.grid2_frame, bg="#000000", bd=2, relief=tk.FLAT)
                sub_frame.grid(row=sb_row, column=sb_col, padx=1, pady=1)
                self.grid2_sub_frames[sub_board_idx] = sub_frame
                
                for spot_row in range(2):
                    for spot_col in range(2):
                        spot_idx = spot_row * 2 + spot_col
                        row = sb_row * 2 + spot_row
                        col = sb_col * 2 + spot_col
                        
                        _btn_size = int(100 * scale)
                        if sub_board_idx == 4:
                            btn = tk.Button(sub_frame, image=self.pixel, width=_btn_size, height=_btn_size,
                                          relief=tk.SUNKEN, bg="#000000", state=tk.DISABLED)
                        else:
                            btn = tk.Button(sub_frame, image=self.pixel, width=_btn_size, height=_btn_size,
                                          relief=tk.RAISED, bg="#3a3a3a",
                                          command=lambda sb=sub_board_idx: self.on_sub_board_click(sb))
                        btn.grid(row=spot_row, column=spot_col)
                        self.grid2_buttons[(row, col)] = btn
        
    def set_controller(self, controller):
        """Set the controller reference after initialization"""
        self.controller = controller
        
    def on_return_menu(self):
        self.app.show_menu()

    def on_piece_click(self, sub_board_idx, spot_idx):
        """Handle when player clicks on a spot to place a piece"""
        if self.controller is None:
            return
            
        # Store the selection
        self.selected_sub_board_idx = sub_board_idx
        self.selected_spot_idx = spot_idx
        
        # Notify controller
        self.controller.handle_piece_click(sub_board_idx, spot_idx)

    def on_sub_board_click(self, source_idx):
        """Handle when player clicks on a sub-board to move"""
        if self.controller is None:
            return
            
        # Store the selection
        self.selected_source_idx = source_idx
        
        # Notify controller
        self.controller.handle_sub_board_click(source_idx)
    
    def update_board_display(self, board_state):
        """Update the 6x6 grid display based on model's board_state
        
        Args:
            board_state: List of 9 sub-boards, each with 4 spots or []
        """
        for sub_board_idx in range(9):
            # Update sub-board frame border
            sub_frame = self.grid1_sub_frames.get(sub_board_idx)
            if sub_frame:
                sub_frame.config(bg="#000000")
        
        for row in range(6):
            for col in range(6):
                sub_board_row = row // 2
                sub_board_col = col // 2
                sub_board_idx = sub_board_row * 3 + sub_board_col
                
                spot_row = row % 2
                spot_col = col % 2
                spot_idx = spot_row * 2 + spot_col
                
                btn = self.grid1_buttons.get((row, col))
                if btn is None:
                    continue
                
                if board_state[sub_board_idx] == []:
                    btn.config(bg="#000000", state=tk.DISABLED, relief=tk.SUNKEN, command=lambda: None)
                else:
                    piece_value = board_state[sub_board_idx][spot_idx]
                    
                    if piece_value == 0:
                        btn.config(bg="#3a3a3a", state=tk.NORMAL, relief=tk.RAISED,
                                  command=lambda sb=sub_board_idx, sp=spot_idx: self.on_piece_click(sb, sp))
                    elif piece_value == 1:
                        btn.config(bg="#FF0000", state=tk.DISABLED, relief=tk.SUNKEN)  # Red
                    elif piece_value == 2:
                        btn.config(bg="#FFFFFF", state=tk.DISABLED, relief=tk.SUNKEN)  # White
    
    def update_sub_board_display(self, possible_sub_board_spots, board_state=None):
        """Update the 6x6 sub-board selector grid showing board state with sub-board border highlights
        
        Args:
            possible_sub_board_spots: List of 9 values (0=unavailable, 1=movable, 2=empty)
            board_state: Current board state from model
        """
        # Update sub-board frame borders
        for sub_board_idx in range(9):
            sub_frame = self.grid2_sub_frames.get(sub_board_idx)
            if sub_frame:
                spot_type = possible_sub_board_spots[sub_board_idx]
                if spot_type == 1:
                    sub_frame.config(bg="#00CC00")  # Green border for movable
                else:
                    sub_frame.config(bg="#000000")  # Black border default
        
        for row in range(6):
            for col in range(6):
                btn = self.grid2_buttons.get((row, col))
                if btn is None:
                    continue
                
                sub_board_row = row // 2
                sub_board_col = col // 2
                sub_board_idx = sub_board_row * 3 + sub_board_col
                
                spot_row = row % 2
                spot_col = col % 2
                spot_idx = spot_row * 2 + spot_col
                
                spot_type = possible_sub_board_spots[sub_board_idx]
                
                if spot_type == 2:
                    btn.config(bg="#000000", state=tk.DISABLED, relief=tk.SUNKEN, command=lambda: None)
                elif board_state is None or board_state[sub_board_idx] == []:
                    btn.config(bg="#000000", state=tk.DISABLED, relief=tk.SUNKEN, command=lambda: None)
                else:
                    piece_value = board_state[sub_board_idx][spot_idx]
                    
                    if spot_type == 1:
                        # Movable - show pieces, clickable
                        if piece_value == 0:
                            btn.config(bg="#3a3a3a", activebackground="#3a3a3a", state=tk.NORMAL, relief=tk.RAISED,
                                      command=lambda sb=sub_board_idx: self.on_sub_board_click(sb))
                        elif piece_value == 1:
                            btn.config(bg="#FF0000", activebackground="#FF0000", state=tk.NORMAL, relief=tk.SUNKEN,
                                      command=lambda sb=sub_board_idx: self.on_sub_board_click(sb))
                        elif piece_value == 2:
                            btn.config(bg="#FFFFFF", activebackground="#FFFFFF", state=tk.NORMAL, relief=tk.SUNKEN,
                                      command=lambda sb=sub_board_idx: self.on_sub_board_click(sb))
                    else:
                        # Unavailable - show pieces, disabled
                        if piece_value == 0:
                            btn.config(bg="#3a3a3a", state=tk.DISABLED, relief=tk.RAISED, command=lambda: None)
                        elif piece_value == 1:
                            btn.config(bg="#FF0000", state=tk.DISABLED, relief=tk.SUNKEN, command=lambda: None)
                        elif piece_value == 2:
                            btn.config(bg="#FFFFFF", state=tk.DISABLED, relief=tk.SUNKEN, command=lambda: None)
    
    def highlight_valid_piece_moves(self, board_state, valid_sub_boards=None):
        """Highlight which pieces can be placed
        
        Args:
            board_state: Current board state from model
            valid_sub_boards: List of sub-board indexes where moves are valid (None = all)
        """
        for row in range(6):
            for col in range(6):
                # Skip center
                if (row == col == 2 or row == col == 3) or (row == 2 and col == 3) or (row == 3 and col == 2):
                    continue
                
                sub_board_row = row // 2
                sub_board_col = col // 2
                sub_board_idx = sub_board_row * 3 + sub_board_col
                
                spot_row = row % 2
                spot_col = col % 2
                spot_idx = spot_row * 2 + spot_col
                
                btn = self.grid1_buttons.get((row, col))
                if btn is None:
                    continue
                
                # Only highlight if sub-board exists and spot is empty
                if board_state[sub_board_idx] != [] and board_state[sub_board_idx][spot_idx] == 0:
                    if valid_sub_boards is None or sub_board_idx in valid_sub_boards:
                        btn.config(state=tk.NORMAL, bg="#5a5a5a")  # Lighter gray for valid moves
                    else:
                        btn.config(state=tk.DISABLED, bg="#2a2a2a")  # Darker gray for invalid
    
    def reset_selection(self):
        """Clear all selection state"""
        self.selected_sub_board_idx = None
        self.selected_spot_idx = None
        self.selected_source_idx = None
    
    def update_status(self, message):
        """Update the status label with a message"""
        self.status_label.config(text=message)
    
    def show_game_result(self, result):
        """Display game result (win/lose/draw)
        
        Args:
            result: String like "Red wins", "White wins", "Draw"
        """
        # Create a popup window
        result_window = tk.Toplevel(self.window)
        result_window.title("Game Over")
        result_window.geometry(f"{int(300 * self.scale)}x{int(150 * self.scale)}")
        
        label = tk.Label(result_window, text=result, font=("Arial", int(20 * self.scale), "bold"))
        label.pack(pady=int(30 * self.scale))
        
        ok_button = tk.Button(result_window, text="OK", font=("Arial", int(11 * self.scale)), command=result_window.destroy)
        ok_button.pack(pady=int(10 * self.scale))

    def show_grid1(self):
        """Show the piece placement grid"""
        self.grid1_frame.tkraise()
        if self.controller and self.controller.model.current_player == 2:
            self.status_label.config(text="Your turn - Place your piece (White)")
        else:
            self.status_label.config(text="AI's turn (Red)")
    
    def show_grid2(self):
        """Show the sub-board selection grid"""
        self.grid2_frame.tkraise()
        self.status_label.config(text="Now select a sub-board to move")

    def show(self):
        self.frame.pack()
        
        # Start with piece placement grid visible
        self.show_grid1()
        
    def hide(self):
        self.frame.pack_forget()

    
class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Four In A Square")

        # Compute scale from screen resolution (baseline: 800px wide window)
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        target = min(screen_w, screen_h) * 0.8
        self.scale = max(0.5, min(2.0, target / 800))

        win_w = int(800 * self.scale)
        win_h = int(900 * self.scale)
        self.window.geometry(f"{win_w}x{win_h}")

        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources\\logo.png")
        logo_img = Image.open(logo_path)
        
        # Create multiple sizes for different contexts
        self.logo_16 = ImageTk.PhotoImage(logo_img.resize((16, 16), Image.Resampling.LANCZOS))
        self.logo_32 = ImageTk.PhotoImage(logo_img)
        self.logo_48 = ImageTk.PhotoImage(logo_img.resize((48, 48), Image.Resampling.LANCZOS))
        self.logo_64 = ImageTk.PhotoImage(logo_img.resize((64, 64), Image.Resampling.LANCZOS))
        self.logo_128 = ImageTk.PhotoImage(logo_img.resize((128, 128), Image.Resampling.LANCZOS))
        self.logo_256 = ImageTk.PhotoImage(logo_img.resize((256, 256), Image.Resampling.LANCZOS))
        
        self.window.iconphoto(True, self.logo_256, self.logo_128, self.logo_64, self.logo_48, self.logo_32, self.logo_16)
        
        self.menu = MainMenuView(self.window, self, scale=self.scale)
        self.game = GameView(self.window, self, controller=None, scale=self.scale)  # Controller set later
        self.controller = None  # Controller reference
        
        self.menu.show()  # Start with menu visible
    
    def set_controller(self, controller):
        """Set the controller reference for the game view"""
        self.controller = controller
        self.game.set_controller(controller)
        
    def show_game(self):
        self.menu.hide()
        self.game.show()
        
        # Start a new game when showing the game view
        if self.controller:
            self.controller.start_new_game()
        
    def show_menu(self):
        self.game.hide()
        self.menu.show()
        
    def run(self):
        self.window.mainloop()