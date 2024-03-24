import asyncio

from parser import Parser
from sys import argv


async def main():
    parser = Parser()
    await parser.query(argv[1])
    print(*parser.albums, sep="\n")


if __name__ == "__main__":
    asyncio.run(main())
