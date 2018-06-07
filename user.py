import asyncio

import protocol

class User:
    def __init__(self, user_data, reader, writer):
        self.nick = user_data["nick"]
        self._reader = reader # asynchronous stream reader of client
        self._writer = writer # asynchronous stream writer

    # send raw data (e.g. prepared json string) to self._writer.
    def _send_raw(self, raw_data):
        self._writer.write(raw_data.encode("utf8"))
        self._writer.write(b'\n')    
    
    # message (dict or str) to json and send to client
    def send_message(self, message):
        json_message = protocol.dump(protocol.new_message(message))
        self._send_raw(json_message)

    # service message dict to json and send
    def send_service(self, service):
        json_service = protocol.dump(service)
        self._send_raw(json_service)

    # returns bool type of message (true if message has type "message" and false if message has type "service")
    # and the message by itself
    async def read_message(self):
        message = await self._reader.readline()
        if not message:
            return None, None
        message_type, parsed_message = protocol.load(message.decode("utf8"))
        if message_type: # type is "message"
            parsed_message["nick"] = self.nick
        return message_type, parsed_message
