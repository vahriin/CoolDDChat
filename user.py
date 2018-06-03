import asyncio
import json

import protocol

class User:
    def __init__(self, user_data, reader, writer):
        self.nick = user_data["nick"]
        self._reader = reader
        self._writer = writer
    
    def send_message(self, message):
        json_message = json.dumps(message)
        self.send_raw(json_message)

    def send_raw(self, raw_data):
        self._writer.write(raw_data.encode("utf8"))
        self._writer.write(b'\n')

    async def read_message(self):
        message = await self._reader.readline()
        if not message:
            return None, None
        message_type, parsed_message = protocol.load(message.decode("utf8"))
        if message_type: # type is "message"
            parsed_message["nick"] = self.nick
        return message_type, parsed_message
