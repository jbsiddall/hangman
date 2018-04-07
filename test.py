import pytest

from hangman import server
from hangman.server import Event, Game, State


@pytest.fixture
def state():
    games = {"game2": Game(word="game2word", guesses=set(), client_ids={0})}
    history = {"game1": Event("game1word", "won"), "game0": Event("game0word", "lost")}
    return State(games, history, next_client_id=1)

def test_create_game(state):
    broadcasts, response = server.apply_command(state, command="create", args=["game3", "hangman"], client_id=0)
    assert Game(word="hangman", guesses=set(), client_ids=set()) == state.games['game3']

def test_create_game_fails_when_game_already_exists(state):
    broadcasts, response = server.apply_command(state, command="create", args=["game2", "hangman"], client_id=0)
    assert Game(word="game2word", guesses=set(), client_ids={0}) == state.games['game2']
    assert "error > game game2 already exists" == response

def test_create_game_fails_when_word_invalid(state):
    invalids = ["", " ", "-", "g*f", "h\nw"]
    for invalid in invalids:
        broadcasts, response = server.apply_command(state, command="create", args=["newgame", invalid], client_id=0)
        assert "newgame" not in state.games
        assert f"error > invalid word '{invalid}'" == response


def test_create_game_fails_when_previous_game_played_has_same_name(state):
    broadcasts, response = server.apply_command(state, command="create", args=["game1", "hangman"], client_id=0)
    assert "game1" not in state.games
    assert "error > game game1 already exists" == response

def test_list(state):
    broadcasts, response = server.apply_command(state, command="list", args=[], client_id=0)
    assert 'game0' in response and 'game1' in response and 'game2' in response
    assert {} == broadcasts

def test_join_game(state):
    broadcasts, response = server.apply_command(state, command="join", args=["game2"], client_id=1)
    assert Game(word="game2word", guesses=set(), client_ids={0, 1}) == state.games['game2']
    assert {} == broadcasts

def test_leave_game(state):
    broadcasts, response = server.apply_command(state, command="leave", args=["game2"], client_id=0)
    assert Game(word="game2word", guesses=set(), client_ids=set()) == state.games['game2']
    assert {} == broadcasts

def test_leave_game_fails_for_game_not_joined(state):
    broadcasts, response = server.apply_command(state, command="leave", args=["game2"], client_id=1)
    assert Game(word="game2word", guesses=set(), client_ids={0}) == state.games['game2']
    assert {} == broadcasts
    assert "error > not playing game game2"

def test_leave_game_fails_for_non_existant_game(state):
    broadcasts, response = server.apply_command(state, command="leave", args=["fakegame"], client_id=0)
    assert {} == broadcasts
    assert "error > fakegame doesnt exist"

def test_guess_char(state):
    broadcasts, response = server.apply_command(state, command="guess", args=["game2", "w"], client_id=0)
    assert Game(word="game2word", guesses=set("w"), client_ids={0}) == state.games['game2']
    assert {"game2": "game2: _____w___ (w) (lives: 8)"} == broadcasts

def test_guess_win_game(state):
    for c in "game2word":
        assert "game2" in state.games
        broadcasts, response = server.apply_command(state, command="guess", args=["game2", c], client_id=0)
    assert {} == state.games
    assert Event("game2", "WON") == state.history['game2']
    assert {"game2": "game2: WON game2word (lives: 8)"} == broadcasts

def test_guess_loose_game(state):
    for c in "zxcvypln":
        assert "game2" in state.games
        broadcasts, response = server.apply_command(state, command="guess", args=["game2", c], client_id=0)
    assert {} == state.games
    assert Event("game2", "LOST") == state.history['game2']
    assert {"game2": "game2: LOST game2word (lives: 0)"} == broadcasts

def test_guess_fails_for_multiple_chars(state):
    broadcasts, response = server.apply_command(state, command="guess", args=["game2", "no"], client_id=0)
    assert Game(word="game2word", guesses=set(), client_ids={0}) == state.games['game2']
    assert {} == broadcasts
    assert "error > can only guess one char at a time" == response

def test_guess_fails_for_game_not_joined(state):
    broadcasts, response = server.apply_command(state, command="guess", args=["game2", "h"], client_id=1)
    assert Game(word="game2word", guesses=set(), client_ids={0}) == state.games['game2']
    assert {} == broadcasts
    assert "error > not joined game2" == response

def test_guess_fails_for_non_existent_game(state):
    broadcasts, response = server.apply_command(state, command="guess", args=["fakegame", "h"], client_id=0)
    assert {} == broadcasts
    assert "error > fakegame doesnt exist" == response

def test_fails_for_unknown_command(state):
    broadcasts, response = server.apply_command(state, command="fake", args=[], client_id=0)
    assert "error > unknown command 'fake'"
