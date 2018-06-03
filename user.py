import asyncio

class User:
    def __init__(self, user_data, reader, writer):
        self.nick = user_data["nick"]
        self._reader = reader
        self._writer = writer
    
    def send_message(self, message):
        json_message = json.dumps(message)
        self._writer.write(json_message.encode("utf8"))
        self._writer.write('\n')

    async def read_message(self):
        message = await reader.readline()
        if not message:
            return None
        parsed_message = json.loads(message.decode("utf8"))
        parsed_message["nick"] = self._nick
        return parsed_message
