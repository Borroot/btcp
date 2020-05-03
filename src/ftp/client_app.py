#!/usr/local/bin/python3

import argparse
from btcp.client_socket import BTCPClientSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-i", "--input", help="File to send", default="input.txt")
    args = parser.parse_args()

    sock = BTCPClientSocket(args.timeout)
    # TODO Write your file transfer client code using your implementation of BTCPClientSocket's connect, send, and disconnect methods.
    if sock.connect():
        print("[client] A connection is established.")
    else:
        print("[client] Error while trying to connect.")

    sock.close()


if __name__ == '__main__':
    main()
