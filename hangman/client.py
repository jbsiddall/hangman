import asyncio
from functools import partial
import sys

from hangman.common import readline, writeline, async_print, async_input, DEFAULT_PORT


async def start():
    await async_print(f'client started on port {DEFAULT_PORT}')
    reader, writer = await asyncio.open_connection(host='localhost', port=DEFAULT_PORT)

    watch_reader = join_pipes(partial(readline, reader), async_print, lambda x: x is None, 'server disconnected')
    watch_input = join_pipes(async_input, partial(writeline, writer), lambda x: len(x) == 0, 'client disconnected')

    await asyncio.gather(watch_reader, watch_input)


async def join_pipes(input_pipe, output_pipe, check_result, error_msg):
    while True:
        line = await input_pipe()
        if check_result(line):
            await async_print(error_msg)
            sys.exit(0)
        await output_pipe(line)
