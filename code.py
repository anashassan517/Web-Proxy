#MUHAMMAD ANAS 20k - 1726
#WARZAN 20k - 1649

import socket
import sys
import time
import os
import threading
from collections import OrderedDict
import json

# Specify the blocked URLs and keywords
blocked =[]
cache=OrderedDict()
cacheSize=10
def cacheGet(key):
    if key in cache:
        return cache[key]
    return False
def cachePut(key,value):
    cache[key]=value
    cache.move_to_end(key)
    if(len(cache)>cacheSize):
        cache.popitem(last=False)
    with open('cache.txt', 'w') as cacheFile:
        cacheFile.write(json.dumps(cache))
    return
def handle_client(client_socket):
    # Receive the request from the client
    request = client_socket.recv(1024).decode('utf-8')
    # parse the second line
    second_line = request.split('\n')[1]
    if('http' in request):
        http(client_socket,request)
        return
    temp=second_line.split(': ')[1]
    port=int(temp.split(':')[1])
    webserver=temp.split(':')[0]
    for blocked_url in blocked:
        if blocked_url in webserver:
            reply = "HTTP/1.1 403 Forbidden \r\n"
            reply += "Proxy-agent: Pyx\r\n"
            reply += "\r\n"
            client_socket.sendall(reply.encode('utf-8'))
            client_socket.close()
            return
    # Create a connection to the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((webserver,port))
    reply = "HTTP/1.0 200 Connection established\r\n"
    reply += "Proxy-agent: Pyx\r\n"
    reply += "\r\n"
    # Send the request to the server
    client_socket.sendall( reply.encode() )
    client_socket.setblocking(0)
    server_socket.setblocking(0)
    while True:
        try:
            request = client_socket.recv(1024)
            if len(request)==0:
                break
            server_socket.sendall( request )
        except socket.error as err:
            pass
        try:
            if len(reply)==0:
                break
            reply = server_socket.recv(1024)
            client_socket.sendall( reply )
        except socket.error as err:
            pass
def http(conn,request):
    # parse the first line
    first_line = request.split('\n')[0]

    # get url
    url = first_line.split(' ')[1]
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):]

    port_pos = temp.find(":")
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos): 
        # default port 
        port = 80 
        webserver = temp[:webserver_pos] 
    else: 
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect((webserver, port))
    s.sendall(request.encode())
    cacheReply=cacheGet(request)
    if cacheReply:
        print('found in cache')
        conn.send(cacheReply.encode())
        return
    else:
        print('cache miss')
    # receive data from web server
    data = s.recv(1024)
    print('original',data.decode())
    cachePut(request,data.decode())
    if (len(data) > 0):
        conn.send(data) # send to browser/client
if __name__ == '__main__':
    with open('blocked_content.txt') as f:
        data = f.read()
        blocked=data.split(' ')
        blocked.remove('')
    data=''
    with open('cache.txt') as f:
        data = f.read()
    if(len(data)!=0):
        cache=json.loads(data)
        cache=OrderedDict(cache)
    prompt = input("Do you want to configure blocked content Press [Y] for YES and [N] for NO :  ")
    if prompt == 'y' or prompt == 'Y':
        blocked = []  # Create a new empty list to hold the blocked websites
        while True:
            block = input("Enter Website to be blocked :   ")
            blocked.append(block)
            with open('blocked_content.txt', 'a') as file_obj:  # Use a different variable name for the file object
                file_obj.write(f'{block} ')
            prompt = input("Do you want to add more ?  ")
            if prompt == 'N' or prompt == 'n':
                break

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip=socket.gethostbyname(socket.gethostname())
    server_socket.bind((ip,5555))
    server_socket.settimeout(1)                  
    print(f"Server started on {ip}:5555")
    server_socket.listen(5)
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print('Accepted connection from {}:{}'.format(client_address[0], client_address[1]))
            # Create a thread to handle the client connection
            client_thread = threading.Thread(target=handle_client, args=(client_socket,),daemon=True)
            client_thread.start()
        except socket.timeout:
            continue
    server_socket.close()