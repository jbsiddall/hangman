import copy
import asyncio
from functools import partial
from collections import namedtuple
from contextlib import contextmanager

from hangman.common import (DEFAULT_PORT, async_print, readline, writeline, GAME_LIVES)


State = namedtuple('State', ['games', 'history', 'next_client_id'])
Game = namedtuple('Game', ['word', 'guesses', 'client_ids'])
Event = namedtuple('Event', ['game_name', 'outcome'])


class Box:
    def __init__(self, *items):
        self.items = items


@contextmanager
def transform(box):
    state, clients = box.items
    updated_state = copy.deepcopy(state)
    updated_clients = copy.copy(clients)
    yield updated_state, updated_clients
    box.items = updated_state, updated_clients


async def start():
    await async_print(f'server started on port {DEFAULT_PORT}')
    state = State(games={}, history={}, next_client_id=[0])
    clients = {}

    server = await asyncio.start_server(
        client_connected_cb=partial(client_handler, Box(state, clients)),
        port=DEFAULT_PORT)
    await server.wait_closed()


async def client_handler(box, reader, writer):

    with transform(box) as (state, clients):
        client_id = add_client(state, clients, client=writer)

    await async_print(f'client {client_id} connected')

    while True:
        line = await readline(reader)
        if line is None:
            await async_print(f'client {client_id} disconnected')
            with transform(box) as (state, clients):
                cleanup_client(state, clients, client_id)
            return
        command, *args = line.split(' ')

        old_state,*_ = box.items
        with transform(box) as (state, clients):
            broadcasts, response = apply_command(state, command, args, client_id)

        if response is not None:
            await writeline(writer, response)

        # need to use old_state because when a game is finished, its moved to history
        # and we loose all the client_ids to broadcast the message to.
        await broadcast_message(old_state, clients, broadcasts)


def add_client(state, clients, client):
    client_id = state.next_client_id[0]
    state.next_client_id[0] = client_id + 1
    clients[client_id] = client
    return client_id


async def broadcast_message(state, clients, broadcasts):
    for game_name, message in broadcasts.items():
        for id in state.games[game_name].client_ids:
            await writeline(clients[id], message)


def cleanup_client(state, clients, client_id):
    del clients[client_id]
    for game in state.games.values():
        if client_id in game.client_ids:
            game.client_ids.remove(client_id)


def apply_command(state, command, args, client_id):
    """returns (broadcasts, response)
    where
    broadcasts is a map from game name to a message to broadcast to all players of that game.
    response is a nullable message to send back to the specific client.
    state will be mutated in place
    """

    commands = {
        'help': help,
        'create': create_game,
        'list': list_game,
        'join': join_game,
        'leave': leave_game,
        'guess': guess,
    }

    if command not in commands:
         return {}, f"error > unknown command '{command}'"
    return commands[command](state, args, client_id)


def help(state, args, client_id):
    msg = "\n".join([
        "help - list all commands",
        "create: game_name word - creates new game",
        "list - lists all active and previous games",
        "join: game_name - joins a game",
        "leave: game_name - leaves a game",
        "guess: game_name char - guesses a character for a game"
    ])
    return {}, "commands:\n" + msg


def create_game(state, args, client_id):
    if len(args) != 2:
        return {}, "error > args: game_name word"

    name, word = args

    if name in state.games or name in state.history:
        return {}, f"error > game {name} already exists"

    cleaned_word = word.lower().strip()
    if len(cleaned_word) == 0 or not all(map(is_alpha, cleaned_word)):
        return {}, f"error > invalid word '{word}'"

    state.games[name] = Game(word=cleaned_word, guesses=set(), client_ids=set())
    return {}, None

def is_alpha(char):
    A, Z = 97, 122
    return A <= ord(char) <= Z

def list_game(state, args, client_id):
    if len(args) != 0:
        return {}, "error > no args expected"

    return {}, "active:\n{}\nhistory:\n{}\n".format(
        '\n'.join(f' * {game}' for game in state.games),
        '\n'.join(f' * {game} ({outcome})' for game,(_,outcome) in state.history.items()))


def join_game(state, args, client_id):
    if len(args) != 1:
        return {}, "error > args: game_name"
    name, = args
    state.games[name].client_ids.add(client_id)
    return {}, None


def leave_game(state, args, client_id):
    if len(args) != 1:
        return {}, "error > args: game_name"

    name, = args

    if name not in state.games:
        return {}, "error > fakegame doesnt exist"

    game = state.games[name]
    if client_id not in game.client_ids:
        return {}, "error > not playing game game2"
    game.client_ids.remove(client_id)
    return {}, None


def guess(state, args, client_id):
    if len(args) != 2:
        return {}, "error > args: game_name char"

    game_name, char = args

    if game_name not in state.games:
        return {}, "error > fakegame doesnt exist"

    game = state.games[game_name]

    if len(char) != 1:
        return {}, "error > can only guess one char at a time"

    if client_id not in game.client_ids:
        return {}, f"error > not joined {game_name}"

    game.guesses.add(char)

    def finish_game(outcome):
        state.history[game_name] = Event(game_name, outcome)
        del state.games[game_name]
        return {game_name: f'{game_name}: {outcome} {game.word} (lives: {lives(game)})'}, None

    if won(game):
        return finish_game('WON')
    elif lost(game):
        return finish_game('LOST')
    else:
        return {game_name: f'{game_name}: {format_guess_line(game)} ({char}) (lives: {lives(game)})'}, None

def won(game):
    return set(game.word).issubset(game.guesses)


def lost(game):
    return lives(game) <= 0


def lives(game):
    return GAME_LIVES - len(set(game.guesses).difference(game.word))

def format_guess_line(game):
    return ''.join(c if c in game.guesses else '_' for c in game.word)
