from __future__ import print_function
from copy import deepcopy
import sys
import numpy as np

## Helper functions

# Translate a position in chess notation to x,y-coordinates
# Example: c3 corresponds to (2,5)
def to_coordinate(notation):
    x = ord(notation[0]) - ord('a')
    y = 8 - int(notation[1])
    return (x, y)

# Translate a position in x,y-coordinates to chess notation
# Example: (2,5) corresponds to c3
def to_notation(coordinates):
    (x,y) = coordinates
    letter = chr(ord('a') + x)
    number = 8 - y
    return letter + str(number)

# Translates two x,y-coordinates into a chess move notation
# Example: (1,4) and (2,3) will become b4c5
def to_move(from_coord, to_coord):
    return to_notation(from_coord) + to_notation(to_coord)

## Defining board states

# These Static classes are used as enums for:
# - Material.Rook
# - Material.King
# - Material.Pawn
# - Side.White
# - Side.Black
class Material:
    Rook, King, Pawn = ['r','k','p']
class Side:
    White, Black = range(0,2)

# A chesspiece on the board is specified by the side it belongs to and the type
# of the chesspiece
class Piece:
    def __init__(self, side, material):
        self.side = side
        self.material = material


# A chess configuration is specified by whose turn it is and a 2d array
# with all the pieces on the board
class ChessBoard:
    
    def __init__(self, turn):
        # This variable is either equal to Side.White or Side.Black
        self.turn = turn
        self.board_matrix = None


    ## Getter and setter methods 
    def set_board_matrix(self,board_matrix):
        self.board_matrix = board_matrix

    # Note: assumes the position is valid
    def get_boardpiece(self,position):
        (x,y) = position
        return self.board_matrix[y][x]

    # Note: assumes the position is valid
    def set_boardpiece(self,position,piece):
        (x,y) = position
        self.board_matrix[y][x] = piece
    
    # Read in the board_matrix using an input string
    def load_from_input(self,input_str):
        self.board_matrix = [[None for _ in range(8)] for _ in range(8)]
        x = 0
        y = 0
        for char in input_str:
            if y == 8:
                if char == 'W':
                    self.turn = Side.White
                elif char == 'B':
                    self.turn = Side.Black
                return
            if char == '\r':
                continue
            if char == '.':
                x += 1
                continue
            if char == '\n':
                x = 0
                y += 1
                continue 
            
            if char.isupper():
                side = Side.White
            else:
                side = Side.Black
            material = char.lower()

            piece = Piece(side, material)
            self.set_boardpiece((x,y),piece)
            x += 1

    # Print the current board state
    def __str__(self):
        return_str = ""

        return_str += "   abcdefgh\n\n"
        y = 8
        for board_row in self.board_matrix:
            return_str += str(y) + "  " 
            for piece in board_row:
                if piece == None:
                    return_str += "."
                else:
                    char = piece.material
                    if piece.side == Side.White:
                        char = char.upper()
                    return_str += char
            return_str += '\n'
            y -= 1
        
        turn_name = ("White" if self.turn == Side.White else "Black") 
        return_str += "It is " + turn_name + "'s turn\n"

        return return_str

    # Given a move string in chess notation, return a new ChessBoard object
    # with the new board situation
    # Note: this method assumes the move suggested is a valid, legal move
    def make_move(self, move_str):
        
        start_pos = to_coordinate(move_str[0:2])
        end_pos = to_coordinate(move_str[2:4])

        if self.turn == Side.White:
            turn = Side.Black
        else:
            turn = Side.White
            
        # Duplicate the current board_matrix
        new_matrix = [row[:] for row in self.board_matrix]
        
        # Create a new chessboard object
        new_board = ChessBoard(turn)
        new_board.set_board_matrix(new_matrix)

        # Carry out the move in the new chessboard object
        piece = new_board.get_boardpiece(start_pos)
        new_board.set_boardpiece(end_pos, piece)
        new_board.set_boardpiece(start_pos, None)

        return new_board

    def is_king_dead(self, side):
        seen_king = False
        for x in range(8):
            for y in range(8):
                piece = self.get_boardpiece((x,y))
                if piece != None and piece.side == side and \
                        piece.material == Material.King:
                    seen_king = True
        return not seen_king
    
    # This function should return, given the current board configuation and
    # which players turn it is, all the moves possible for that player
    # It should return these moves as a list of move strings, e.g.
    # [c2c3, d4e5, f4f8]
    def legal_moves(self):
        move_list = []
        for x in range(8):
            for y in range(8):
                piece = self.get_boardpiece((x,y))
                if piece != None and piece.side == self.turn:
                    all_moves = self.all_moves((x,y))
                    for move in all_moves:
                        if self.is_legal_move(move):
                            move_list.append(move)
        return move_list


    # Generates all possible moves from a start coordinate, without taking
    # the rules of the game into account
    def all_moves(self, coordinates):
        moves = []
        for i in range(8):
            for j in range(8):
                moves.append(to_move(coordinates,(i,j)))
        return moves

    # This function should return, given the move specified (in the format
    # 'd2d3') whether this move is legal
    def is_legal_move(self, move):
        start = to_coordinate(move[:2])
        end = to_coordinate(move[2:])
        if self.outside_board(start, end):
            return False
        if self.spot_occupied(start, end):
            return False
        if self.piece_restriction(start, end):
            return False
        return True

    # Checks whether a spot is occupied by teammate, by oppenent or a free spot
    def spot_occupied(self, start_pos, end_pos):
        piece = self.get_boardpiece(start_pos)
        piece_end = self.get_boardpiece(end_pos)

        if piece_end == None or piece_end.side != piece.side:
            return False
        else:
            return True

    # Checks if the proposed move starts, and stays inside the chess board.
    def outside_board(self, start, end):
        if 0 > start[0] > 7 or 0 > start[1] > 7:
            return True
        elif 0 > end[0] > 7 or 0 > end[1] > 7:
            return True
        elif end == start:
            return True
        return False

    # Checks if the proposed path of movement lies within the options of the
    # piece.
    def piece_restriction(self, start, end):
        piece = self.get_boardpiece(start)

        if self.turn != piece.side:
            return True

        if None == piece:
            return True

        elif Material.Pawn == piece.material:
            if end[1] - start[1] != 1:
                return True

            if start[0] - end[0] != 0:
                if self.get_boardpiece(end):
                    return False
                else:
                    return True

        elif Material.Rook == piece.material:
            if start[0] - end[0] != 0:
                if start[1] - end[1] != 0:
                    return True
            elif start[1] - end[1] != 0:
                if start[0] - end[0]:
                    return True
            return False

        else:
            if abs(start[0] - end[0]) > 1:
                return True
            if abs(start[1] - end[1]) > 1:
                return True
            return False


# This static class is responsible for providing functions that can calculate
# the optimal move using minimax
class ChessComputer:

    # This method uses either alphabeta or minimax to calculate the best move
    # possible. The input needed is a chessboard configuration and the max
    # depth of the search algorithm. It returns a tuple of (score, chessboard)
    # with score the maximum score attainable and chessboardmove that is needed
    #to achieve this score.
    @staticmethod
    def computer_move(chessboard, depth, alphabeta=False):
        if alphabeta:
            inf = 99999999
            min_inf = -inf
            return ChessComputer.alphabeta(chessboard, depth, min_inf, inf)
        else:
            return ChessComputer.minimax(chessboard, depth)


    # This function uses minimax to calculate the next move. Given the current
    # chessboard and max depth, this function should return a tuple of the
    # the score and the move that should be executed
    # NOTE: use ChessComputer.evaluate_board() to calculate the score
    # of a specific board configuration after the max depth is reached
    @staticmethod
    def minimax(chessboard, depth):
        possible_moves = ChessBoard.legal_moves(chessboard)
        best_move = possible_moves[0]
        best_score = 0
        for move in possible_moves:
            new_board = ChessBoard.make_move(chessboard, move)
            if chessboard.turn == Side.Black:
                score = ChessComputer.max_value(new_board, depth)
                if score < best_score:
                    best_move = move
                    best_score = score
            else:
                score = ChessComputer.min_value(new_board, depth)
                if score > best_score:
                    best_move = move
                    best_score = score
        return best_score, best_move

    @staticmethod
    def min_value(chessboard, depth):
        depth -= 1
        if ChessBoard.is_king_dead(chessboard, chessboard.turn):
            return ChessComputer.evaluate_board(chessboard, depth)
        possible_moves = ChessBoard.legal_moves(chessboard)
        if depth == 1:
            scores = ChessComputer.scores(chessboard, possible_moves, depth)
            return min(scores)
        best = 9999999
        for move in possible_moves:
            new_board = ChessBoard.make_move(chessboard, move)
            value = ChessComputer.max_value(new_board, depth)
            if value < best:
                best = value
        return best

    @staticmethod
    def max_value(chessboard, depth):
        depth -= 1
        if ChessBoard.is_king_dead(chessboard, chessboard.turn):
            return ChessComputer.evaluate_board(chessboard, depth)
        possible_moves = ChessBoard.legal_moves(chessboard)
        if depth == 1:
            scores = ChessComputer.scores(chessboard, possible_moves, depth)
            return min(scores)
        best = -9999999
        for move in possible_moves:
            new_board = ChessBoard.make_move(chessboard, move)
            value = ChessComputer.min_value(new_board, depth)
            if value > best:
                best = value
        return best


    @staticmethod
    def scores(chessboard, possible_moves, depth):
        scores = []
        for move in possible_moves:
            new_board = ChessBoard.make_move(chessboard, move)
            scores.append(ChessComputer.evaluate_board(new_board, depth))
        return scores




    # This function uses alphabeta to calculate the next move. Given the
    # chessboard and max depth, this function should return a tuple of the
    # the score and the move that should be executed.
    # It has alpha and beta as extra pruning parameters
    # NOTE: use ChessComputer.evaluate_board() to calculate the score
    # of a specific board configuration after the max depth is reached
    @staticmethod
    def alphabeta(chessboard, depth, alpha, beta):
        return ChessComputer.minimax(chessboard, depth)
        return (0, "no implementation written")

    # Calculates the score of a given board configuration based on the 
    # material left on the board. Returns a score number, in which positive
    # means white is better off, while negative means black is better of
    @staticmethod
    def evaluate_board(chessboard, depth_left):
        white_score = ChessComputer.count_pieces(chessboard, Side.White)
        black_score = ChessComputer.count_pieces(chessboard, Side.Black)
        weight = ChessComputer.get_weight(depth_left)
        score =  weight * (white_score - black_score)
        return score

    # Calculate weight
    @staticmethod
    def get_weight(depth_left):
        return depth_left

    # Counts the pieces of a specified color, assigns a score to each piece,
    # and returns the score
    @staticmethod
    def count_pieces(chessboard, side):
        score = 0
        for i in range(8):
            for j in range(8):
                piece = ChessBoard.get_boardpiece(chessboard, (i,j))
                if piece != None and piece.side == side:
                    score += ChessComputer.get_score(piece.material)
        return score

    # Get the score of a specific material
    @staticmethod
    def get_score(material):
        score = 0
        if material == Material.Pawn:
            score += 1
        elif material == Material.Rook:
            score += 5
        else:
            score += 50
        return score



# This class is responsible for starting the chess game, playing and user
# feedback
class ChessGame:
    def __init__(self, turn):
     
        # NOTE: you can make this depth higher once you have implemented
        # alpha-beta, which is more efficient
        self.depth = 4
        self.chessboard = ChessBoard(turn)

        # If a file was specified as commandline argument, use that filename
        if len(sys.argv) > 1:
            filename = sys.argv[1]
        else:
            filename = "board.chb"

        print("Reading from " + filename + "...")
        self.load_from_file(filename)

    def load_from_file(self, filename):
        with open(filename) as f:
            content = f.read()

        self.chessboard.load_from_input(content)

    def main(self):
        while True:
            print(self.chessboard)

            # Print the current score
            score = ChessComputer.evaluate_board(self.chessboard,self.depth)
            print("Current score: " + str(score))
            
            # Calculate the best possible move
            new_score, best_move = self.make_computer_move()
            
            print("Best move: " + best_move)
            print("Score to achieve: " + str(new_score))
            print("")
            self.make_human_move()


    def make_computer_move(self):
        print("Calculating best move...")
        return ChessComputer.computer_move(self.chessboard,
                self.depth, alphabeta=True)
        

    def make_human_move(self):
        # Endlessly request input until the right input is specified
        print(self.chessboard.legal_moves())
        while True:
            if sys.version_info[:2] <= (2, 7):
                move = raw_input("Indicate your move (or q to stop): ")
            else:
                move = input("Indicate your move (or q to stop): ")
            if move == "q":
                print("Exiting program...")
                sys.exit(0)
            elif self.chessboard.is_legal_move(move):
                break
            print("Incorrect move!")

        self.chessboard = self.chessboard.make_move(move)

        # Exit the game if one of the kings is dead
        if self.chessboard.is_king_dead(Side.Black):
            print(self.chessboard)
            print("White wins!")
            sys.exit(0)
        elif self.chessboard.is_king_dead(Side.White):
            print(self.chessboard)
            print("Black wins!")
            sys.exit(0)

chess_game = ChessGame(Side.White)
chess_game.main()

