import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from chessgpt import Board, rules

# Helper to play a sequence of moves on the board
def play(board, moves):
    for uci in moves:
        board.make_move(rules.Move.from_uci(uci))

# ----- Castling -----
@pytest.mark.parametrize("fen, move", [
    ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1"),
    ("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1c1"),
    ("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1", "e8g8"),
])
def test_castling_legal(fen, move):
    board = Board(fen)
    mv = rules.Move.from_uci(move)
    assert mv in board.get_legal_moves()


@pytest.mark.parametrize("fen, move", [
    ("r3k2r/8/8/6r1/8/8/8/R3K2R w KQkq - 0 1", "e1g1"),  # through attack
    ("r3k2r/8/8/8/8/8/8/R3KN1R w KQkq - 0 1", "e1g1"),  # piece blocking
    ("r3k2r/8/8/8/8/8/8/R3K2R w Q - 0 1", "e1g1"),      # rights missing
])
def test_castling_illegal(fen, move):
    board = Board(fen)
    mv = rules.Move.from_uci(move)
    assert mv not in board.get_legal_moves()

# ----- En passant -----
@pytest.mark.parametrize("sequence, capture", [
    (['e2e4', 'a7a6', 'e4e5', 'd7d5'], 'e5d6'),
    (['d2d4', 'a7a6', 'd4d5', 'e7e5'], 'd5e6'),
    (['c2c4', 'a7a6', 'c4c5', 'd7d5'], 'c5d6'),
])
def test_en_passant_legal(sequence, capture):
    board = Board()
    play(board, sequence)
    mv = rules.Move.from_uci(capture)
    assert mv in board.get_legal_moves()


@pytest.mark.parametrize("sequence, capture", [
    (['e2e4', 'a7a6', 'e4e5', 'd7d5', 'h2h3'], 'e5d6'),
    (['e2e4', 'a7a6', 'e4e5', 'h7h6'], 'e5d6'),
    (['e2e4', 'a7a6', 'e4e5', 'd7d6', 'a2a3'], 'e5d6'),
])
def test_en_passant_illegal(sequence, capture):
    board = Board()
    play(board, sequence)
    mv = rules.Move.from_uci(capture)
    assert mv not in board.get_legal_moves()

# ----- Promotion -----
@pytest.mark.parametrize("fen, move, piece", [
    ("8/P7/8/8/8/8/7p/7K w - - 0 1", "a7a8q", 'Q'),
    ("7k/8/8/8/8/8/p6P/7K b - - 0 1", "a2a1n", 'n'),
    ("8/1P6/8/8/8/8/7p/7K w - - 0 1", "b7b8r", 'R'),
])
def test_promotion_legal(fen, move, piece):
    board = Board(fen)
    mv = rules.Move.from_uci(move)
    assert mv in board.get_legal_moves()
    board.make_move(mv)
    assert board.state.board[rules.square_index(move[2:4])] == piece


@pytest.mark.parametrize("fen, move", [
    ("8/8/P7/8/8/8/7p/7K w - - 0 1", "a6a7q"),        # not on last rank
    ("8/P7/8/8/8/8/7p/7K w - - 0 1", "a7a8k"),        # invalid piece
    ("8/8/8/R7/8/8/8/7K w - - 0 1", "a4a8q"),        # rook promotion attempt
])
def test_promotion_illegal(fen, move):
    board = Board(fen)
    mv = rules.Move.from_uci(move)
    assert mv not in board.get_legal_moves()

# ----- Fifty-move rule -----
@pytest.mark.parametrize("halfmove, expected", [
    (0, False),
    (99, False),
    (100, True),
])
def test_fifty_move_rule_detection(halfmove, expected):
    fen = f"8/8/8/8/8/8/8/K1k5 w - - {halfmove} 1"
    board = Board(fen)
    assert board.is_draw_by_fifty_moves() is expected

