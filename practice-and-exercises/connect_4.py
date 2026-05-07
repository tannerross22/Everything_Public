
import numpy as np

ROW_COUNT = 6
COLUMN_COUNT = 7


def create_board():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT))
    return board


board = create_board()
game_over = False
turn = 0


def drop_piece(board, row, col, piece):
    board[row][col] = piece


def is_valid(board, col):
    return board[ROW_COUNT-1][col] == 0


def next_open_row(board, col):
    for i in range(ROW_COUNT):
        if board[i][col] == 0:
            return i


def print_board(board):
    print(np.flip(board, 0))


def winning_move(board,peice):
    # check horizontal first
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT):
            if board[r][c] == peice and board[r][c+1] == peice and board[r][c+2] == peice and board[r][c+3] == peice:
                return True
    # check for vertical win
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT-3):
            if board[r][c] == peice and board[r+1][c] == peice and board[r+2][c] == peice and board[r+3][c] == peice:
                return True
    # positive slope diagonal
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT-3):
            if board[r][c] == peice and board[r+1][c+1] == peice and board[r+2][c+2] == peice and board[r+3][c+3] == peice:
                return True
    # negative slope diagonal
    for c in range(COLUMN_COUNT-3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == peice and board[r-1][c+1] == peice and board[r-2][c+2] == peice and board[r-3][c+3] == peice:
                return True


while not game_over:
    # ask for player one input
    if turn == 0:
        col = int(input("Player one selection (0-6): "))
        if col in range(COLUMN_COUNT):
            if is_valid(board, col):
                row = next_open_row(board, col)
                drop_piece(board, row, col, 1)
                if winning_move(board, 1):
                    print("Player one wins")
                    print_board(board)
                    break
        else:
            print("Please enter a valid column")
            turn = 1

    # ask for player two input
    else:
        col = int(input("Player two selection (0-6): "))
        if col in range(COLUMN_COUNT):
            if is_valid(board, col):
                row = next_open_row(board, col)
                drop_piece(board, row, col, 2)
                if winning_move(board, 2):
                    print("Player two wins")
                    print_board(board)
                    break
            else:
                print("Please enter a valid column")
                turn = 0
    print_board(board)
    turn += 1
    turn = turn % 2

