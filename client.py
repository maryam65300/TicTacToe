import socket
import json
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

class TicTacToeClient:
    def __init__(self):
        self.socket = None
        self.player_num = None
        self.symbol = None
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 0
        self.game_over = False
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe - Client")
        self.root.geometry("400x500")
        
        self.buttons = []
        self.status_label = tk.Label(self.root, text="Connecting...", font=('Arial', 14))
        self.status_label.pack(pady=10)
        
        self.create_board()
        self.create_controls()
        
    def create_board(self):
        self.board_frame = tk.Frame(self.root)
        self.board_frame.pack(pady=20)
        
        for i in range(3):
            button_row = []
            for j in range(3):
                button = tk.Button(
                    self.board_frame, 
                    text=' ', 
                    font=('Arial', 20, 'bold'),
                    width=3, 
                    height=2,
                    command=lambda r=i, c=j: self.make_move(r, c)
                )
                button.grid(row=i, column=j, padx=2, pady=2)
                button_row.append(button)
            self.buttons.append(button_row)
            
    def create_controls(self):
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=20)
        
        self.restart_button = tk.Button(
            self.control_frame,
            text="Restart Game",
            font=('Arial', 12),
            command=self.restart_game
        )
        self.restart_button.pack(side=tk.LEFT, padx=10)
        
        self.quit_button = tk.Button(
            self.control_frame,
            text="Quit",
            font=('Arial', 12),
            command=self.quit_game
        )
        self.quit_button.pack(side=tk.LEFT, padx=10)
        
    def connect_to_server(self):
        host = simpledialog.askstring("Server IP", "Enter server IP (default: localhost):", initialvalue="localhost")
        if not host:
            host = "localhost"
            
        port = 12345
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            # Start listening for messages
            listen_thread = threading.Thread(target=self.listen_to_server)
            listen_thread.daemon = True
            listen_thread.start()
            
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            return False
            
    def listen_to_server(self):
        try:
            while True:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                message = json.loads(data)
                self.handle_server_message(message)
                
        except Exception as e:
            print(f"Error listening to server: {e}")
            
    def handle_server_message(self, message):
        if message['type'] == 'welcome':
            self.player_num = message['player_num']
            self.symbol = message['symbol']
            self.root.title(f"Tic Tac Toe - Player {self.player_num + 1} ({self.symbol})")
            self.update_status(f"Connected as Player {self.player_num + 1} ({self.symbol}). Waiting for opponent...")
            
        elif message['type'] == 'game_state':
            self.board = message['board']
            self.current_player = message['current_player']
            self.game_over = message['game_over']
            
            self.root.after(0, self.update_gui)
            
            if self.game_over:
                winner = message['winner']
                if winner is None:
                    self.root.after(0, lambda: self.update_status("Game Over - It's a Draw!"))
                elif winner == self.player_num:
                    self.root.after(0, lambda: self.update_status("Game Over - You Win!"))
                else:
                    self.root.after(0, lambda: self.update_status("Game Over - You Lose!"))
            else:
                if self.current_player == self.player_num:
                    self.root.after(0, lambda: self.update_status("Your turn!"))
                else:
                    self.root.after(0, lambda: self.update_status("Opponent's turn..."))
                    
    def update_gui(self):
        for i in range(3):
            for j in range(3):
                self.buttons[i][j]['text'] = self.board[i][j]
                
    def update_status(self, text):
        self.status_label.config(text=text)
        
    def make_move(self, row, col):
        if (self.current_player == self.player_num and 
            not self.game_over and 
            self.board[row][col] == ' '):
            
            move_message = {
                'type': 'move',
                'row': row,
                'col': col
            }
            self.send_to_server(move_message)
            
    def restart_game(self):
        restart_message = {'type': 'restart'}
        self.send_to_server(restart_message)
        
    def send_to_server(self, message):
        try:
            self.socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            print(f"Error sending to server: {e}")
            
    def quit_game(self):
        if self.socket:
            self.socket.close()
        self.root.quit()
        
    def run(self):
        if self.connect_to_server():
            self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
            self.root.mainloop()
        else:
            self.root.destroy()

if __name__ == "__main__":
    client = TicTacToeClient()
    client.run()