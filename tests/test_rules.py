import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chessgpt import Board, rules


def test_check_move_allowed():
    fen = "4r2k/8/8/8/8/8/4R3/4K3 w - - 0 1"
    board = Board(fen)
    check_move = rules.Move.from_uci("e2e8")
    assert check_move in board.get_legal_moves()


def test_move_leaving_king_in_check_disallowed():
    fen = "4r2k/8/8/8/8/8/4R3/4K3 w - - 0 1"
    board = Board(fen)
    illegal_move = rules.Move.from_uci("e2f2")
    assert illegal_move not in board.get_legal_moves()
