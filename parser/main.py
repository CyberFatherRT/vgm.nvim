from parser import Parser
from sys import argv

if __name__ == "__main__":
    parser = Parser()
    parser.query(argv[1])
    print(*parser.albums, sep="\n")
