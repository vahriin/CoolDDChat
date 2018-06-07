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

def form_service(attr={}):
    service_message = {"type": "service"}
    service_message.update(attr)
    return service_message

# form status. ext_inf must be str with error info. 
# message_id must be id of delievered message.
# if message id not passed to function, result will not 
# contain "messageId" field
def new_status(code=200, ext_inf=None, message_id=None):
    status = form_service({"status": code})
    if code != 200:
        status["error_code"] = code
        if ext_inf != None:
            status["error_info"] = ext_inf
        else:
            status["error_info"] = STATUSES[code]

    if message_id != None:
        status["messageId"] = message_id

    return status

# form message dict from string
def form_message(attr={}):
    message = {"type": "message"}
    message.update(attr)
    return message

# the "message" arg must be dict (e.g. {"type":"message", "message": "bla-bla"})
# of string that contains text of message (e.g. "bla-bla")
def new_message(message):
    if type(message) == str:
        message = {"message": message}
    return form_message(message)


def dump(message):
    return json.dumps(message)

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