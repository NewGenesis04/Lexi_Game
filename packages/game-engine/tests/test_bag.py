from game_engine.bag import build_bag, draw_tiles, exchange_tiles # type: ignore
from game_engine.models import Tile # type: ignore

# --- build_bag ---

def test_build_bag_total_count():
    assert len(build_bag()) == 100

def test_build_bag_letter_distribution():
    counts: dict[str, int] = {}
    for tile in build_bag():
        counts[tile.letter] = counts.get(tile.letter, 0) + 1

    assert counts["A"] == 9
    assert counts["E"] == 12
    assert counts["Q"] == 1
    assert counts["Z"] == 1
    assert counts[" "] == 2   # blanks

def test_build_bag_point_values():
    by_letter = {t.letter: t.points for t in build_bag()}
    assert by_letter["A"] == 1
    assert by_letter["D"] == 2
    assert by_letter["B"] == 3
    assert by_letter["F"] == 4
    assert by_letter["K"] == 5
    assert by_letter["J"] == 8
    assert by_letter["Q"] == 10
    assert by_letter["Z"] == 10
    assert by_letter[" "] == 0

def test_build_bag_returns_tile_instances():
    assert all(isinstance(t, Tile) for t in build_bag())

# --- draw_tiles ---

def test_draw_tiles_count():
    bag = build_bag()
    drawn, remaining = draw_tiles(bag, 7)
    assert len(drawn) == 7
    assert len(remaining) == 93

def test_draw_tiles_no_mutation():
    bag = build_bag()
    snapshot = list(bag)
    draw_tiles(bag, 7)
    assert bag == snapshot

def test_draw_tiles_clamps_to_bag_size():
    small_bag = build_bag()[:5]
    drawn, remaining = draw_tiles(small_bag, 10)
    assert len(drawn) == 5
    assert remaining == []

def test_draw_tiles_empty_bag():
    drawn, remaining = draw_tiles([], 7)
    assert drawn == []
    assert remaining == []

def test_draw_tiles_zero():
    bag = build_bag()
    drawn, remaining = draw_tiles(bag, 0)
    assert drawn == []
    assert len(remaining) == 100

def test_draw_tiles_preserves_total():
    bag = build_bag()
    drawn, remaining = draw_tiles(bag, 7)
    assert len(drawn) + len(remaining) == 100

# --- exchange_tiles ---

def test_exchange_tiles_preserves_total():
    bag = build_bag()
    drawn, bag = draw_tiles(bag, 7)
    to_return, kept = drawn[:3], drawn[3:]
    new_drawn, new_bag = exchange_tiles(bag, to_return, 3)
    assert len(new_drawn) + len(new_bag) + len(kept) == 100

def test_exchange_tiles_drawn_count():
    bag = build_bag()
    _, bag = draw_tiles(bag, 7)
    new_drawn, _ = exchange_tiles(bag, [], 3)
    assert len(new_drawn) == 3

def test_exchange_tiles_returned_tiles_enter_pool():
    bag = build_bag()
    drawn, bag = draw_tiles(bag, 7)
    to_return = drawn[:3]
    new_drawn, new_bag = exchange_tiles(bag, to_return, 3)
    full_pool = new_drawn + new_bag
    # every returned tile's letter must appear somewhere in the new pool
    for tile in to_return:
        assert any(t.letter == tile.letter and t.points == tile.points for t in full_pool)
