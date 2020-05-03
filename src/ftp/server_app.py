#!/usr/local/bin/python3

import argparse
from btcp.server_socket import BTCPServerSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-o", "--output", help="Where to store the file", default="output.txt")
    args = parser.parse_args()

    sock = BTCPServerSocket(args.window)
    # TODO Write your file transfer server code here using your BTCPServerSocket's accept, and recv methods.
    sock.accept()
    print("[server] A connection is established.")

    sock.close()


if __name__ == '__main__':
    main()
