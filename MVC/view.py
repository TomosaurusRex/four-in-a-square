import tkinter as tk
from PIL import Image, ImageTk
import controller
import os

class MainMenuView:
    def __init__(self, window):
        self.window = window
        self.frame = tk.Frame(self.window)
        
        self.start_game_button = tk.Button(self.frame, text="Start Game", command=self.on_start_game)
        self.start_game_button.pack(pady=20)
        # TODO: Add title, buttons, etc.
        
    def on_start_game(self):
        self.window.controller.show_game()

    def show(self):
        self.frame.pack()
        
    def hide(self):
        self.frame.pack_forget()


class GameView:
    def __init__(self, window):
        self.window = window
        self.frame = tk.Frame(self.window)
        
        self.canvas = tk.Canvas(self.frame, width=700, height=700, bg="white")
        self.canvas.pack()
        
        self.status_label = tk.Label(self.frame, text="Welcome to Four In A Square!")
        self.status_label.pack()
        
        # TODO: Add game elements

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

        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logo.png")
        logo_img = Image.open(logo_path)
        
        # Create multiple sizes for different contexts
        self.logo_16 = ImageTk.PhotoImage(logo_img.resize((16, 16), Image.Resampling.LANCZOS))
        self.logo_32 = ImageTk.PhotoImage(logo_img)
        self.logo_48 = ImageTk.PhotoImage(logo_img.resize((48, 48), Image.Resampling.LANCZOS))
        self.logo_64 = ImageTk.PhotoImage(logo_img.resize((64, 64), Image.Resampling.LANCZOS))
        self.logo_128 = ImageTk.PhotoImage(logo_img.resize((128, 128), Image.Resampling.LANCZOS))
        self.logo_256 = ImageTk.PhotoImage(logo_img.resize((256, 256), Image.Resampling.LANCZOS))
        
        self.window.iconphoto(True, self.logo_256, self.logo_128, self.logo_64, self.logo_48, self.logo_32, self.logo_16)
        
        # Give views access to controller methods
        self.window.controller = self
        
        self.menu = MainMenuView(self.window)
        self.game = GameView(self.window)
        
        self.menu.show()  # Start with menu visible
        
    def show_game(self):
        self.menu.hide()
        self.game.show()
        
    def show_menu(self):
        self.game.hide()
        self.menu.show()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()