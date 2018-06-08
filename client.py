import asyncio
import sys
import json
import argparse

import protocol

# asynchronous reader for stdin
async def create_stdin_reader():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader(loop=loop)
    async_protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
    await loop.connect_read_pipe(lambda: async_protocol, sys.stdin)
    return reader

class Client:
    def __init__(self, host, port):
        self._nick = ""
        self._reader = None
        self._writer = None
        self._non_deliver_messages = 0
        self._loop = asyncio.get_event_loop()
        self._input_reader = self._loop.run_until_complete(create_stdin_reader())
        try:
            self._loop.run_until_complete(self._loop.create_task(self.connect(host, port)))
            self._loop.run_forever()
        except OSError:
            print("Error: Cannot connect to server.")
            exit()
        except protocol.ProtocolException:
            print("Error: Connection broken")
            exit()
        except KeyboardInterrupt:
            self._loop.stop()
            print()

        
    async def connect(self, host, port):
        self._reader, self._writer = await asyncio.open_connection(host, port, loop=self._loop)
        _type, response = protocol.load((await self._reader.readline()).decode("utf8"))
        if not response["status"]:
            print("Server refused connection with: {}".format(response["error"]))
        await self.registration()
    
    async def registration(self):
        error = ""
        while error != None:
            print("Enter your nick: ", end='')
            sys.stdout.flush()
            self._nick = await self.ainput()
            self._writer.write(protocol.dump(protocol.form_service({"nick": self._nick})).encode("utf8"))
            self._writer.write(b'\n')
            
            nick_response = await self._reader.readline()
            _type, response = protocol.load(nick_response.decode("utf8"))
            error = protocol.check_error(response)
            if error != None:
                print(protocol.check_error(response))
        print("Welcome to chat, {}!\n".format(self._nick))
        handle_stdin_task = self._loop.create_task(self.handle_stdin())
        handle_message_task = self._loop.create_task(self.handle_message())
        
    async def ainput(self):
        return (await self._input_reader.readline()).decode("utf8").replace("\r", "").replace("\n", "")        

    async def handle_stdin(self):
        while True:
            message = await self.ainput()
            self._writer.write(protocol.dump(protocol.new_message(message)).encode("utf8"))
            self._writer.write(b'\n')
            self._non_deliver_messages += 1
            
    async def handle_message(self):
        while True:
            try:
                message_type, message = protocol.load((await self._reader.readline()).decode("utf8"))
            except protocol.ProtocolException:
                print("Connection broken. Press Ctrl-C to exit")
                return
            if message_type == None: # connection is break
                return
            elif message_type: # message_type is "message"
                self.message_handler(message)
            else: # message_type is "service"
                self.service_handler(message)
    
    def message_handler(self, message):
        print("{}: {}\n".format(message["nick"], message["message"]))
        sys.stdout.flush()
        self._writer.write(protocol.dump(protocol.new_status(message_id=message["messageId"])).encode("utf8"))
        self._writer.write(b'\n')

    def service_handler(self, service):
        if service.get("status") == None: # got user list (somebody connect or disconnect)
            # this feature can be extended for displaying message like 
            # "<user> (connected to)/(disconnected from) chat"
            print("Active clients: {}".format(",".join(service["users"])))
        elif protocol.check_error(service) == None: # got message status
            print("Message delievered to: {}".format(",".join(service["users"])))


def new_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", default='localhost')
    parser.add_argument("-p", "--port", default='59503')
    return parser

if __name__ == '__main__':
    parser = new_parser()
    namespace = parser.parse_args(sys.argv[1:])
    client = Client(namespace.server, namespace.port)

