# HANGMAN

## INSTALL

```
git clone <...> hangman
cd hangman
python3.6 -m venv .
./bin/pip3 install -r requirements.txt.
```

## TESTS 

```
./bin/pytest test.py
```

## SERVER

```
./bin/python3 -m hangman server
```

## CLIENT

```
./bin/python3 -m hangman client
```

## HOW TO PLAY

Client is a repl and you can see what commands are available by typing `help` and hitting enter:

```
commands:
help - list all commands
create: game_name word - creates new game
list - lists all active and previous games
join: game_name - joins a game
leave: game_name - leaves a game
guess: game_name char - guesses a character for a game
```


Example of a game:

Client 1

```
create myfirstgame hello
join myfirstgame
```

Client 2:

```
list
join myfirstgame
guess myfirstgame h
guess myfirstgame e
guess myfirstgame l
guess myfirstgame 0
```
