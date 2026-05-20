import socket
import threading
import json

class TicTacToeServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 0  # 0 for X, 1 for O
        self.game_over = False
        self.winner = None
        
    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(2)
        
        print(f"Server listening on {self.host}:{self.port}")
        print("Waiting for 2 players to connect...")
        
        while len(self.clients) < 2:
            client_socket, addr = server_socket.accept()
            self.clients.append(client_socket)
            player_num = len(self.clients) - 1
            symbol = 'X' if player_num == 0 else 'O'
            
            print(f"Player {player_num + 1} ({symbol}) connected from {addr}")
            
            # Send welcome message
            welcome_msg = {
                'type': 'welcome',
                'player_num': player_num,
                'symbol': symbol,
                'message': f'You are Player {player_num + 1} ({symbol})'
            }
            self.send_to_client(client_socket, welcome_msg)
            
            # Start handling this client
            thread = threading.Thread(target=self.handle_client, args=(client_socket, player_num))
            thread.start()
        
        print("Both players connected! Game starting...")
        self.start_game()
        
    def handle_client(self, client_socket, player_num):
        try:
            while not self.game_over:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                message = json.loads(data)
                
                if message['type'] == 'move':
                    self.process_move(message, player_num)
                elif message['type'] == 'restart':
                    self.restart_game()
                    
        except Exception as e:
            print(f"Error handling client {player_num}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            
    def process_move(self, message, player_num):
        if self.current_player != player_num or self.game_over:
            return
            
        row, col = message['row'], message['col']
        
        if self.board[row][col] == ' ':
            symbol = 'X' if player_num == 0 else 'O'
            self.board[row][col] = symbol
            
            # Check for win or draw
            if self.check_winner():
                self.game_over = True
                self.winner = player_num
            elif self.is_board_full():
                self.game_over = True
                self.winner = None  # Draw
            else:
                self.current_player = 1 - self.current_player
            
            # Broadcast game state to all clients
            self.broadcast_game_state()
            
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return True
                
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return True
                
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return True
            
        return False
        
    def is_board_full(self):
        return all(cell != ' ' for row in self.board for cell in row)
        
    def start_game(self):
        self.broadcast_game_state()
        
    def restart_game(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 0
        self.game_over = False
        self.winner = None
        self.broadcast_game_state()
        
    def broadcast_game_state(self):
        game_state = {
            'type': 'game_state',
            'board': self.board,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner
        }
        
        for client in self.clients:
            self.send_to_client(client, game_state)
            
    def send_to_client(self, client_socket, message):
        try:
            client_socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            print(f"Error sending to client: {e}")

if __name__ == "__main__":
    server = TicTacToeServer()
    server.start_server()