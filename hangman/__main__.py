import asyncio
import sys
from hangman import server, client


if __name__ == '__main__':
    mode = server.start() if sys.argv[1] == 'server' else client.start()
    asyncio.get_event_loop().run_until_complete(mode)
    asyncio.get_event_loop().close()
