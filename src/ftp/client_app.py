#!/usr/local/bin/python3

from btcp.client_socket import BTCPClientSocket
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-i", "--input", help="File to send", default="input.txt")
    args = parser.parse_args()

    sock = BTCPClientSocket(args.timeout)

    def close(exit_status):
        sock.close()
        exit(exit_status)

    if sock.connect():
        print("[client] A connection is established.")
    else:
        print("[client] Error while trying to connect.")
        close(1)

    with open(args.input, 'r', encoding='utf-8') as file:
        data = file.read()
    if sock.send(data):
        print("[client] The data is successfully transferred.")
    else:
        print("[client] Error while trying to transfer the data.")

    if sock.disconnect():
        print("[client] The connection is terminated.")
    else:
        print("[client] The connection is terminated abnormally.")
        close(1)
    close(0)


if __name__ == '__main__':
    main()
