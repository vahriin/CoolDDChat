import asyncio
import sys
import json

import protocol

async def create_stdin_reader():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader(loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return reader

class Client:
    def __init__(self, host, port):
        self._reader = None
        self._writer = None
        self._non_deliver_messages = 0
        self._loop = asyncio.get_event_loop()
        self._input_reader = self._loop.run_until_complete(create_stdin_reader())
        self._loop.run_until_complete(self._loop.create_task(self.connect(host, port)))
        self._loop.run_forever()

        
    async def connect(self, host, port):
        self._reader, self._writer = await asyncio.open_connection(host, port, loop=self._loop)
        _type, response = protocol.load((await self._reader.readline()).decode("utf8"))
        if not response["status"]:
            print("Server refused connection with: {}".format(response["error"]))
        await self.register()
    
    async def register(self):
        error = ""
        while error != None:
            nick = await self.ainput()
            self._writer.write(protocol.new_service({"nick": nick}).encode("utf8"))
            self._writer.write(b'\n')
            nick_response = await self._reader.readline()
            _type, response = protocol.load(nick_response.decode("utf8"))
            error = protocol.check_error(response)
            if error != None:
                print(protocol.check_error(response))
        print("connected")
        handle_stdin_task = self._loop.create_task(self.handle_stdin())
        handle_message_task = self._loop.create_task(self.handle_message())
        
    async def ainput(self):
        return (await self._input_reader.readline()).decode("utf8").replace("\r", "").replace("\n", "")        

    async def handle_stdin(self):
        while True:
            message = await self.ainput()
            self._writer.write(protocol.new_message(message).encode("utf8"))
            self._writer.write(b'\n')
            self._non_deliver_messages += 1
            
    async def handle_message(self):
        while True:
            message_type, message = protocol.load((await self._reader.readline()).decode("utf8"))
            if message_type == None:
                return
            elif message_type: # message_type is "message"
                self.message_handler(message)
            else: # message_type is "service"
                self.service_handler(message)
    
    def message_handler(self, message):
        print("{}: {}".format(message["nick"], message["message"]))
        self._writer.write(protocol.new_status_message(message["messageId"]).encode("utf8"))
        self._writer.write(b'\n')

    def service_handler(self, message):
        if protocol.check_error(message) == None:
            self._non_deliver_messages -= 1



client = Client('127.0.0.1', 2805)

