# CoolDDChat

Best app for linux console chating

## Requirements

* Python 3.6

## Installation and run

```
git clone https://github.com/vahriin/CoolDDChat.git
cd CoolDDChat
```
If your Python 3.6 runs as a `python` use

```
python server.py
``` 

to run server with default (59503) port. You can set listen port like this:
```
python server.py -p your_port
```
e.g. 
```
python server.py -p 3333
```
to set listen port is 3333.

Use  
```
python client.py -s server_ip -p port
``` 
to run client, e.g.
```
python client.py -s 192.168.1.3 -p 3333
```

default values of `-s` is 'localhost' and -p is 59503.




