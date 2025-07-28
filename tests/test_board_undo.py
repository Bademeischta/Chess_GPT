import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chessgpt import Board, rules


def snapshot(state):
    return (
        tuple(state.board),
        state.to_move,
        frozenset(state.castling_rights),
        state.en_passant,
        state.halfmove_clock,
        state.fullmove_number,
    )


def test_undo_simple_move():
    board = Board()
    before = snapshot(board.state)
    board.make_move(rules.Move.from_uci("e2e4"))
    board.undo_move()
    assert snapshot(board.state) == before


def test_undo_castling():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    board = Board(fen)
    before = snapshot(board.state)
    board.make_move(rules.Move.from_uci("e1g1"))
    board.undo_move()
    assert snapshot(board.state) == before


def test_undo_en_passant():
    board = Board()
    board.make_move(rules.Move.from_uci("e2e4"))
    board.make_move(rules.Move.from_uci("a7a6"))
    board.make_move(rules.Move.from_uci("e4e5"))
    board.make_move(rules.Move.from_uci("d7d5"))
    before = snapshot(board.state)
    board.make_move(rules.Move.from_uci("e5d6"))
    board.undo_move()
    assert snapshot(board.state) == before


def test_undo_promotion():
    fen = "8/P7/8/8/8/8/7p/7K w - - 0 1"
    board = Board(fen)
    before = snapshot(board.state)
    board.make_move(rules.Move.from_uci("a7a8q"))
    board.undo_move()
    assert snapshot(board.state) == before
