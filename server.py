import asyncio
import json

import user
import status
 
class ChatServer(object):
    def __init__(self, host, port):
        self._let_connecting = True
        self._clients = {}
        self._loop = asyncio.get_event_loop()
        self._server = self._loop.run_until_complete(
            asyncio.start_server(self.accept_connection, host=host, port=port)
        )
        self._loop.run_forever()

    async def accept_connection(self, reader, writer):
        print("conn accepted!")
        if self._let_connecting:
            writer.write(status.new().encode("utf8"))
            writer.write(b'\n')
            await self.register_user(reader, writer)
        else:
            writer.write(status.new("Sorry, connection forbidden").encode("utf8"))
            writer.write(b'\n')

    async def register_user(self, reader, writer):
        client = b""
        while True:
            try:
            
                client = await self.get_client(reader, writer)
                self._clients[client.nick]
                writer.write(status.new("Nick already exists").encode("utf8"))
                writer.write(b'\n')
            except KeyError:
                self._clients[client.nick] = client
                print("user {} connected".format(client.nick))
                #await self.read_handler(client)


    async def get_client(self, reader, writer):
        user_data = (await reader.readline()).decode("utf8")
        user_data = json.loads(user_data)
        client = user.User(user_data, reader, writer)
        return client

    async def read_handler(self, user):
        while True:
            message = await user.read_message()
            if message == None:
                self._clients.remove(user)
                return
            self.broadcast(message)

    def broadcast(self, message):
        for client_nick in self._clients:
            self._clients[client_nick].send_message(message)


if __name__ == '__main__':
    server = ChatServer('127.0.0.1', 2805)
