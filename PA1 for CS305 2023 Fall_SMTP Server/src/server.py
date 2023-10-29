from __future__ import annotations

from argparse import ArgumentParser
# from email.mime.text import MIMEText
from queue import Queue
import socket
from socketserver import ThreadingTCPServer, BaseRequestHandler
from threading import Thread

import tomli


def student_id() -> int:
    return 12112729  # TODO: replace with your SID


parser = ArgumentParser()
parser.add_argument('--name', '-n', type=str, required=True)
parser.add_argument('--smtp', '-s', type=int)
parser.add_argument('--pop', '-p', type=int)

args = parser.parse_args()

with open('data/config.toml', 'rb') as f:
    _config = tomli.load(f)
    SMTP_PORT = args.smtp or int(_config['server'][args.name]['smtp'])
    POP_PORT = args.pop or int(_config['server'][args.name]['pop'])
    ACCOUNTS = _config['accounts'][args.name]
    MAILBOXES = {account: [] for account in ACCOUNTS.keys()}

with open('data/fdns.toml', 'rb') as f:
    FDNS = tomli.load(f)

ThreadingTCPServer.allow_reuse_address = True


def fdns_query(domain: str, type_: str) -> str | None:
    domain = domain.rstrip('.') + '.'
    return FDNS[type_][domain]


class POP3Server(BaseRequestHandler):
    def handle(self):
        conn = self.request
        conn.sendall(b'+OK POP3 server ready.\r\n')
        username = None
        password = None
        to_dele = []
        while True:
            data = conn.recv(1024).decode().strip()
            print(data)
            if not data:
                break

            elif data == 'QUIT':
                for i in to_dele:
                    del MAILBOXES[username][i - 1]
                to_dele = []
                conn.sendall(b'+OK \r\n')
                break

            elif data.startswith('USER'):
                username = data[5:].strip()
                if username not in ACCOUNTS.keys():
                    conn.sendall(b'-ERR invalid username/password\r\n')
                else:
                    conn.sendall(b'+OK \r\n')

            elif data.startswith('PASS'):
                password = data[5:].strip()
                if password != ACCOUNTS[username]:
                    conn.sendall(b'-ERR invalid username/password\r\n')
                else:
                    conn.sendall(b'+OK user successfully logged on\r\n')

            elif data == 'STAT':
                msg_num = 0
                msg_size = 0
                for i, _ in enumerate(MAILBOXES[username], start=1):
                    if i not in to_dele:
                        msg_num += 1
                        msg_size += len(_)
                conn.sendall(f'+OK {msg_num} {msg_size}\r\n'.encode())
            
            elif data == 'LIST':
                conn.sendall(b'+OK\r\n')
                for i, _ in enumerate(MAILBOXES[username], start=1):
                    if i not in to_dele:
                        conn.sendall(f'{i} {len(_)}\r\n'.encode())
                conn.sendall(b'.\r\n')
            
            elif data.startswith('LIST'):
                msg_index = int(data[5:])
                if msg_index > len(MAILBOXES[username]) or msg_index < 1 or msg_index in to_dele:
                    conn.sendall(b'-ERR no such message\r\n')
                else:
                    conn.sendall(b'+OK ' + str(msg_index).encode() + b' ' + str(len(MAILBOXES[username][msg_index - 1])).encode() + b'\r\n')

            elif data.startswith('RETR'):
                msg_index = int(data[5:])
                if msg_index > len(MAILBOXES[username]) or msg_index < 1 or msg_index in to_dele:
                    conn.sendall(b'-ERR no such message\r\n')
                else:
                    mail_content = MAILBOXES[username][msg_index - 1]
                    print(mail_content)
                    conn.sendall(f'+OK \r\n{mail_content}\r\n'.encode())

            elif data.startswith('DELE'):
                msg_index = int(data[5:])
                if msg_index > len(MAILBOXES[username]) or msg_index < 1:
                    conn.sendall(b'-ERR no such message\r\n')
                else:
                    to_dele.append(msg_index)
                    conn.sendall(b'+OK message deleted\r\n')

            elif data == 'RSET':
                to_dele = []
                conn.sendall(b'+OK maildrop has 0 messages (0 octets)\r\n')

            elif data == 'NOOP':
                conn.sendall(b'+OK\r\n')

            else:
                conn.sendall(b'-ERR command not supported\r\n')


# Transfer mails between smtp servers
class SMTPClient:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
    
    def send(self, data: str):
        self.sock.sendall(data.encode())
    
    def quit(self):
        self.sock.close()


class SMTPServer(BaseRequestHandler):
    def handle(self):
        conn = self.request
        conn.sendall(b'220 SMTP server ready\r\n')
        sender = None
        receptors = []
        content = None
        while True:
            data = conn.recv(1024).decode().strip()
            print(data)
            if not data:
                break

            elif data.startswith('helo' or 'ehlo'):
                conn.sendall(b'250 Hello\r\n')

            elif data.startswith('mail FROM'):
                sender = data[10:].strip()
                conn.sendall(b'250 OK From\r\n')

            elif data.startswith('rcpt TO'):
                receptor = data[8:].strip()
                # Verify the existence of receptor's domain
                if (receptor[1:-1].split('@')[-1]+'.') not in FDNS['MX'].keys():
                    print(receptor[1:-1].split('@')[-1])
                    print('not in MX')
                    conn.sendall(b'250 Invaild receptor\r\n')
                # Verify the existence of receptor's account
                elif receptor[1:-1] not in _config['accounts'][_config['agent'][receptor[1:-1].split('@')[-1]]['pop'][4:]].keys():
                    print(receptor[1:-1])
                    print('not in accounts')
                    conn.sendall(b'250 Invaild receptor\r\n')
                else:
                    receptors.append(receptor)
                    conn.sendall(b'250 OK Rcpt\r\n')

            elif data == 'data':
                conn.sendall(b'354 End data with <CR><LF>.<CR><LF>\r\n')
                data = conn.recv(1024).decode().strip()
                print(data)
                content = data
                # if there is no receptor, send back an error and mail it back to the sender
                if len(receptors) == 0:
                    conn.sendall(b'554 Error: no valid recipients\r\n')
                    receptors.append(sender)

                for receptor in receptors:
                    if receptor[1:-1] not in ACCOUNTS.keys():
                        # transfer to another server
                        host = fdns_query(receptor[1:-1].split('@')[-1], 'MX')
                        port = int(fdns_query(host, 'P'))
                        client = SMTPClient('localhost', port)
                        client.send(f'helo {args.name}\r\n')
                        while True:
                            data = client.sock.recv(1024).decode().strip()
                            print(data)
                            if data == '250 Hello':
                                client.send(f'mail FROM:{sender}\r\n')
                            elif data == '250 OK From':
                                client.send(f'rcpt TO:{receptor}\r\n')
                            elif data == '250 OK Rcpt':
                                client.send('data\r\n')
                            elif data == '354 End data with <CR><LF>.<CR><LF>':
                                client.send(content + '\r\n')
                            elif data == '250 OK Receive Data':
                                client.send('quit\r\n')
                            elif data == '221 Bye':
                                break
                        client.quit()

                    else:
                        MAILBOXES[receptor[1:-1]].append(content)
                conn.sendall(b'250 OK Receive Data\r\n')

            elif data == 'quit':
                conn.sendall(b'221 Bye\r\n')
                break

            else:
                conn.sendall(b'500 Error: bad syntax\r\n')


if __name__ == '__main__':
    if student_id() % 10000 == 0:
        raise ValueError('Invalid student ID')

    smtp_server = ThreadingTCPServer(('', SMTP_PORT), SMTPServer)
    pop_server = ThreadingTCPServer(('', POP_PORT), POP3Server)
    Thread(target=smtp_server.serve_forever).start()
    Thread(target=pop_server.serve_forever).start()
