import json

STATUSES = {
    200: "OK",
    400: "Bad requests",
    409: "Nick already exists",
    403: "Forbidden",
    418: "Unclassified error"
    
}

class ProtocolException(Exception):
    def __init__(self, message):
        super().__init__(message, None)

def new_service(attr): #attr must be dict
    attr["type"] = "service"
    return json.dumps(attr)

# form status
def new_status(code=200, ext_inf=None):
    if code == 200:
        return json.dumps({"type": "service", "status": code})
    elif code == 418:
        return json.dumps({"type": "service", "status": code, "error": "{}: {}".format(STATUSES[code], ext_inf)})
    else:
        return json.dumps({"type": "service", "status": code, "error": "{}".format(STATUSES[code])})

# form status of message delivery
def new_status_message(message_id, code=200, ext_inf=None):
    if code == 200:
        return json.dumps({"type": "service", "status": code, "messageId" : message_id})
    elif code == 418:
        return json.dumps({"type": "service", "status": code, "messageId": message_id,
             "error": "{}: {}".format(STATUSES[code], ext_inf)})
    else:
        return json.dumps({"type": "service", "status": code, "messageId": message_id,
             "error": "{}".format(STATUSES[code])})

# the "message" arg must be dict (e.g. {"type":"message", "message": "bla-bla"})
# of string that contains text of message (e.g. "bla-bla")
def new_message(message): 
    if type(message) == str:
        message = _form_message(message)
    message["type"] = "message"
    return json.dumps(message)
    
# form message dict from string
def _form_message(message):
    return {"message": message}


def load(json_protocol):
    try:
        parsed_protocol = json.loads(json_protocol)
        _type = parsed_protocol["type"]
        return _type == "message", parsed_protocol
    except json.JSONDecodeError:
        raise ProtocolException("Non-JSON message detected")
    except KeyError:
        raise ProtocolException('Missing "type" field')

def check_error(parsed_protocol):
    if parsed_protocol["status"] // 100 == 2:
        return None
    return parsed_protocol["error"]