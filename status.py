import json

def new(error=None):
    if error == None:
        return json.dumps({"status": True})
    else:
        return json.dumps({"status": False, "error": error})

def check_error(json_status):
    parsed_status = json.loads(status)
    if parsed_status["status"]:
        return None
    else:
        return parsed_status["error"] 
