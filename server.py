import asyncio
import json
from itertools import cycle

import user
import protocol

class ChatServer:
    def __init__(self, host, port):
        self._let_connecting = True
        self._clients = {}
        self._messages = {}
        self._cycle = cycle([x for x in range(1000)])
        self._loop = asyncio.get_event_loop()
        self._server = self._loop.run_until_complete(
            asyncio.start_server(self.accept_connection, host=host, port=port)
        )
        self._loop.run_forever()

    async def accept_connection(self, reader, writer):
        print("conn accepted!")
        if self._let_connecting:
            writer.write(protocol.new_status().encode("utf8"))
            writer.write(b'\n')
            try:
                await self.register_client(reader, writer)
            except protocol.ProtocolException as pe:
                writer.write(protocol.new_status(418, str(pe)).encode("utf8"))
                writer.write(b'\n')
        else:
            writer.write(protocol.new_status(403).encode("utf8"))
            writer.write(b'\n')

    async def register_client(self, reader, writer):
        client = b""
        try:
            while True:
                client = await self.get_client(reader, writer)
                self._clients[client.nick]
                writer.write(protocol.new_status(409).encode("utf8"))
                writer.write(b'\n')
        except KeyError:
            self._clients[client.nick] = client
            print("user {} connected".format(str(client.nick)))
            writer.write(protocol.new_status().encode("utf8"))
            writer.write(b'\n')
            await self.client_handler(client)

    async def get_client(self, reader, writer):
        user_data = (await reader.readline()).decode("utf8")
        _type, user_data = protocol.load(user_data)
        client = user.User(user_data, reader, writer)
        return client

    async def client_handler(self, client):
        while True:
            message_type, message = await client.read_message()
            if message_type == None:
                return
            elif message_type: # message_type is "message"
                self.message_handler(message, client)
            else: # message_type is "service"
                self.service_handler(message, client)

    def message_handler(self, message, client):
        message_id = next(self._cycle)
        self._messages[message_id] = 0
        #client.send_raw(protocol.new_status_message(message_id))
        message["messageId"] = message_id
        self.broadcast(message, client.nick)

    def broadcast(self, message, author_nick):
        print("{}: {}".format(author_nick, message["message"]))
        for client_nick in self._clients:
            if client_nick != author_nick:
                self._clients[client_nick].send_message(message)

    def service_handler(self, message, client):
        self._messages[message["messageId"]] += 1
        if len(self._messages) <= self._messages[message["messageId"]]:
            self._messages.pop(message["messageId"])
            client.send_raw(protocol.new_status_message(message["messageId"]))

        


if __name__ == '__main__':
    server = ChatServer('127.0.0.1', 2805)
