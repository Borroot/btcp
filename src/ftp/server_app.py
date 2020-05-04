#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=5)
    parser.add_argument("-o", "--output", help="Where to store the file", default="output.txt")
    args = parser.parse_args()

    sock = BTCPServerSocket(args.window)

    sock.accept()
    print("[server] A connection is established.")

    data = sock.recv()
    with open(args.output, 'w', encoding='utf-8') as file:
        file.write(data)

    print("[server] The connection is terminated.")
    sock.close()


if __name__ == '__main__':
    main()
