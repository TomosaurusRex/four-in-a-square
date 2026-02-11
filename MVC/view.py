import tkinter as tk
from PIL import Image, ImageTk
import os
from controller import GameController

class MainMenuView:
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.frame = tk.Frame(self.window)
        
        self.grid1_frame = tk.Frame(self.frame)
        self.grid2_frame = tk.Frame(self.frame)

        pixel = tk.PhotoImage(width=1, height=1)

        for row in range(6):
            for col in range(6):
                if (row == col == 2 or row == col == 3) or (row == 2 and col == 3) or (row == 3 and col == 2):
                    btn = tk.Button(self.grid1_frame, image=pixel, width=100, height=100, relief=tk.SUNKEN, bg="#000000")
                    btn.grid(row=row, column=col)
                else:
                    btn = tk.Button(self.grid1_frame, image=pixel, width=100, height=100, relief=tk.RAISED, bg="#3a3a3a")
                    btn.grid(row=row, column=col)

        for row in range(3):
            for col in range(3):
                if row == col:
                    btn = tk.Button(self.grid2_frame, image=pixel, width=200, height=200, relief=tk.SUNKEN, bg="#000000")
                    btn.grid(row=row, column=col)
                else:
                    btn = tk.Button(self.grid2_frame, image=pixel, width=200, height=200, relief=tk.RAISED, bg="#3a3a3a")
                    btn.grid(row=row, column=col)

        self.start_game_button = tk.Button(self.frame, text="Start Game", command=self.on_start_game)
        self.start_game_button.pack(pady=20)
        # TODO: Add title, buttons, etc.
        
    def on_start_game(self):
        self.app.show_game()

    def show(self):
        self.frame.pack()
        
    def hide(self):
        self.frame.pack_forget()


class GameView:
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.frame = tk.Frame(self.window)

        self.return_menu_button = tk.Button(self.frame, text="Return to Menu", command=self.on_return_menu)
        self.return_menu_button.pack(pady=20)
        
        # TODO: Add game elements
    def on_return_menu(self):
        self.app.show_menu()

    def on_sub_board_click(self):
        pass

    def on_piece_click(self):
        pass

    def show(self):
        self.frame.pack()
        
    def hide(self):
        self.frame.pack_forget()

    
class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Four In A Square")
        self.window.geometry("720x720")

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
        
        self.menu = MainMenuView(self.window, self)
        self.game = GameView(self.window, self)
        
        self.menu.show()  # Start with menu visible
        
    def show_game(self):
        self.menu.hide()
        self.game.show()
        
    def show_menu(self):
        self.game.hide()
        self.menu.show()
        
    def run(self):
        self.window.mainloop()