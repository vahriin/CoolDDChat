import asyncio
import argparse
import sys
import logging
import re

from itertools import cycle

import user
import protocol

class ChatServer:
    def __init__(self, host, port):
        """Chat room for clients. Attributes:
        - host: ip address of server
        - port: port for connection
        """

        # Connected clients. Key is nick, value is User object
        self._clients = {}
        # Delivering messages. The message will be removed whet it is delivered to all clients 
        self._messages = {}
        # Cycle for sequential number of messages
        self._cycle = cycle([x for x in range(1000)])

        self._loop = asyncio.get_event_loop()
        self._server = self._loop.run_until_complete(
            asyncio.start_server(self.accept_connection, host=host, port=port)
        )

    def start(self):
        self._loop.run_forever()

    def stop(self):
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.stop()

    async def accept_connection(self, reader, writer):
        try:
            writer.write(protocol.dump(protocol.new_status()).encode("utf8"))
            writer.write(b'\n')
            try:
                await self.register_client(reader, writer)
            except protocol.ProtocolException as pe:
                writer.write(protocol.dump(protocol.new_status(418, str(pe))).encode("utf8"))
                writer.write(b'\n')
        except BrokenPipeError:
            return

    async def register_client(self, reader, writer):
        client = b""
        try:
            while True:
                # ProtocolException will be raised if client disconnect during this
                client = await self.get_client(reader, writer)
                # check nick
                if client == None:
                    writer.write(protocol.dump(
                            protocol.new_status(410, "Nick should contains only letters or digits")
                        ).encode("utf8"))
                    writer.write(b'\n')
                    continue 
                self._clients[client.nick] # check this nick in clients dict
                writer.write(protocol.dump(protocol.new_status(409)).encode("utf8"))
                writer.write(b'\n')
        except KeyError:
            writer.write(protocol.dump(protocol.new_status()).encode("utf8"))
            writer.write(b'\n')

            self._clients[client.nick] = client
            logging.info("User {} connected.".format(client.nick))
            self.broadcast_clients()
            await self.client_handler(client)

    async def get_client(self, reader, writer):
        user_data = (await reader.readline()).decode("utf8")
        _type, data = protocol.load(user_data)
        try:
            if not re.match(r"^[A-Za-z0-9]+$", data["nick"]):
                return None
            client = user.User(data, reader, writer)
        except KeyError:
            writer.write(protocol.dump(
                protocol.new_status(418, 'Registration request should contains "nick" field')
            ).encode("utf8"))
        return client

    async def client_handler(self, client):
        while True:
            message_type, message = await client.read_message()
            if message_type == None: #connection is broken
                logging.info("User {} disconnected.".format(client.nick))
                self._clients.pop(client.nick) # delete user from clients
                self.broadcast_clients()
                return
            elif message_type: # message_type is "message"
                self.message_handler(message, client)
            else: # message_type is "service"
                self.service_handler(message, client)

    def message_handler(self, message, client):
        message_id = next(self._cycle)
        
        self._messages[message_id] = {"clients_got": 1, "author": client.nick} 
        
        message["messageId"] = message_id
        self.broadcast(message)

    def broadcast(self, message): # message should contain "nick" field
        logging.info("User {} said: {}".format(message["nick"], message["message"]))
        for client_nick in self._clients:
            if client_nick != message["nick"]:
                self._clients[client_nick].send_message(message)

    def broadcast_clients(self):
        for client_nick in self._clients:
            self._clients[client_nick].send_service(protocol.form_service({"users": list(self._clients.keys())}))

    def service_handler(self, message, client):
        self._messages[message["messageId"]]["clients_got"] += 1
        if len(self._clients) <= self._messages[message["messageId"]]["clients_got"]:
            author_nick = self._messages.pop(message["messageId"])["author"]
            status = protocol.new_status()
            status["users"] = []
            for user in self._clients.keys():
                if user != client.nick:
                    status["users"].append(user)
            self._clients[author_nick].send_service(status)

        
def new_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default="59503")
    return parser

if __name__ == '__main__':
    parser = new_parser()
    namespace = parser.parse_args(sys.argv[1:])

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    server = ChatServer('', namespace.port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print()
    
        


