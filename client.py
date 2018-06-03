import asyncio
import sys
import json

import status

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
        self._loop = asyncio.get_event_loop()
        self._input_reader = self._loop.run_until_complete(create_stdin_reader())
        self._loop.run_until_complete(self._loop.create_task(self.connect(host, port)))

        
    async def connect(self, host, port):
        self._reader, self._writer = await asyncio.open_connection(host, port, loop=self._loop)
        response = await self._reader.readline()
        error = status.check_error(response.decode("utf8"))
        if error != None:
            print("Server refused connection with: {}".format(error))
            return
        await self.register()
    
    async def register(self):
        error = ""
        while error != None:
            nick = await self._input_reader.readline()
            nick_request = json.dumps({"nick" : str(nick)})
            self._writer.write(nick_request.encode("utf8"))
            self._writer.write(b'\n')
            nick_response = await self._reader.readline()
            error = status.check_error(nick_response.decode("utf8"))
            if error != None:
                print (error)
        print("connected")
        read_stdin_task = self._loop.create_task(read_stdin)
        
        

    async def read_stdin(self):
        while True:
            raw_message = await self._input_reader.readline()
            message = json.dumps({"message": raw_message})
            self._writer.write(message.encode("utf8"))
            


    async def message_handler(self):
        while True:
            data = json.loads((await self._reader.readline()).decode("utf8"))


client = Client('127.0.0.1', 2805)

