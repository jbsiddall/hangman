import asyncio
import sys

DEFAULT_PORT = 8000
GAME_LIVES = 8

async def writeline(writer, msg):
    writer.write(bytes(msg + '\n', 'utf-8'))
    await writer.drain()

async def readline(reader):
    line = await reader.readline()
    if len(line) == 0:
        return None
    else:
        return str(line, 'utf-8').strip()

async def async_input():
    return (await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)).strip()

async def async_print(msg):
    await asyncio.get_event_loop().run_in_executor(None, sys.stdout.write, msg + '\n')
