"""
    Python 3
    Usage: python3 TCPClient3.py server_IP server_port client_udp_server_port
    coding: utf-8
    
    Author: Pritan Barai 
    - Code referenced from RUI LI assignment demos
"""
from collections import defaultdict
from datetime import datetime
import random
from socket import *
from threading import Thread
from _thread import *
import sys
import json
import os

path = f'{os.getcwd()}/'
file_info = defaultdict(int)

# Command functions
def edg(user:str, cmd_str:str):
    try:
        cmd,file_id,data_amount = cmd_str.split(' ')
    except ValueError:
        print('EDG command requires fileID and dataAmount as arguments.')
        return
    try:
        file_id = int(file_id)
        data_amount = int(data_amount)    
    except ValueError:
        print('the fileID or dataAmount are not integers, you need to specify the parameter as integers.')
        return
    
    print(f'The edge device is generating {data_amount} data samples…')
    
    filename = f'{user}-{file_id}.txt'
    with open(filename, "w+") as file:
        for n in range(data_amount):
            file.write(f'{random.randint(1,100)}\n')
    print(f'Data generation done, {data_amount} data samples have been generated and stored in the file {filename}\n')

    file_info[file_id] = data_amount


def ued(user:str, cmd_str:str):
    try:
        cmd,file_id = cmd_str.split(' ')
    except ValueError:
        print('fileID is needed to upload the data')
        return

    try:
        file_id = int(file_id)   
    except ValueError:
        print('the fileID is not an integer, you need to specify the parameter as an integers.')
        return

    filename = f'{user}-{file_id}.txt'
    if not os.path.isfile(path + filename):
        print('the file to be uploaded does not exist')
        return

    with(open(filename, 'rb')) as file:
        content = file.read()

    request['action'] = 'UED'
    request['user'] = user
    request['data'] = content.decode()
    request['file_id'] = file_id
    request['data_amount'] = file_info[int(file_id)]

    clientSocket.sendall(json.dumps(request).encode())

    data = clientSocket.recv(1024)
    reply = json.loads(data.decode())
    print(reply['msg'])


def scs(user:str, cmd_str:str):
    try:
        cmd,file_id,operation = cmd_str.split(' ')
        file_id = int(file_id)
    except ValueError:
        print('fileID is missing or fileID is not an integer')
        return
    
    request['action'] = 'SCS'
    request['user'] = user
    request['operation'] = operation
    request['file_id'] = file_id
    
    clientSocket.sendall(json.dumps(request).encode())

    data = clientSocket.recv(1024)
    reply = json.loads(data.decode())
    print(reply['msg'])

def dte(user:str, cmd_str:str):
    try:
        cmd,file_id = cmd_str.split(' ')
        file_id = int(file_id)
    except ValueError:
        print('fileID is missing or fileID is not an integer')
        return
    
    request['action'] = 'DTE'
    request['user'] = user
    request['file_id'] = file_id
    request['data_amount'] = file_info[int(file_id)]

    clientSocket.sendall(json.dumps(request).encode())
    print(f'{user} issued DTE command, the file ID is {file_id}')

    data = clientSocket.recv(1024)
    reply = json.loads(data.decode())
    print(reply['msg'])

def aed(user:str, if_print:bool)->str:
    request['action'] = 'AED'
    request['user'] = user
    
    clientSocket.sendall(json.dumps(request).encode())
    data = clientSocket.recv(1024)
    reply = json.loads(data.decode())
    
    if if_print == True:
        print(reply['msg'])

    return reply['msg']
    
def out(user:str, clientSocket:socket):
    request['action'] = 'OUT'
    request['user'] = user

    clientSocket.sendall(json.dumps(request).encode())
    data = clientSocket.recv(1024)
    reply = json.loads(data.decode())
    print(reply['msg'])
    # close the socket
    clientSocket.close()
    exit()

# get IP and UDP port if device is active
def get_UDP_port(user:str, audience:str):
    result = (None, None)
    aed_str = aed(user, False)
    username, ip_address, UDP_port_number, active_since = aed_str.split("; ")
    if username == audience:
        result = (ip_address, UDP_port_number)

    return result

def uvf(user:str, cmd_str:str):
    try:
        cmd,audience,filename = cmd_str.split(' ')
    except ValueError:
        print('incorrect input: UVF deviceName filename')
        return
    ip_address, UDP_port = get_UDP_port(user, audience)

    if ip_address == None or UDP_port == None:
        print(f'{audience} is offline')
        return

    if not os.path.isfile(path + filename):
        print('the file to be uploaded does not exist')
        return
    
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    host = ip_address
    port = int(UDP_port)
    addr = (host, port)

    file_size = os.path.getsize(path + filename)
    print(file_size)
    
    clientSocket.sendto(filename.encode(), addr)
    clientSocket.sendto(user.encode(), addr)
    clientSocket.sendto(str(file_size).encode(), addr)

    f = open(filename, "rb")
    data = f.read(2048)
    while(data):
        if(clientSocket.sendto(data, addr)):
            data = f.read(2048)

    clientSocket.close()
    f.close()

    print(f'{filename} has been uploaded')
    return
    
def udpserver(UDP_port):
    start_new_thread(recv_uvf, ())

def recv_uvf():
    while True:
        host = '127.0.0.1'
        serverSocket = socket(AF_INET, SOCK_DGRAM) # UDP socket
        serverSocket.bind((host, int(UDP_port))) # bind UDP addr and port number
        
        data,addr = serverSocket.recvfrom(2048)
        filename = data.decode().strip()
        
        data,addr = serverSocket.recvfrom(2048)
        presenter = data.decode().strip()

        data,addr = serverSocket.recvfrom(2048)
        file_size = int(data.decode().strip())

        filename = f'{presenter}_{filename}'
        f = open(filename, "wb")
        data,addr = serverSocket.recvfrom(2048)
        try:
            while(data):
                f.write(data)
                serverSocket.settimeout(2)
                data,addr = serverSocket.recvfrom(2048)
        except timeout:
            f.close()
            serverSocket.close()
            uvf_file_size = os.path.getsize(path + filename)
            if uvf_file_size == file_size:
                print(f"\nReceived {filename} from {presenter}\nEnter one of the following commands (EDG, UED, SCS, DTE, AED, UVF, OUT): ", end = '')
                break

def run_command(user:str, clientSocket:socket):
    while True:
        cmd_str = input('Enter one of the following commands (EDG, UED, SCS, DTE, AED, UVF, OUT): ')
        cmd = cmd_str[:3]
        if cmd == 'EDG':
            edg(user, cmd_str)            
        elif cmd == 'UED':
            ued(user, cmd_str)
        elif cmd == 'SCS':
            scs(user, cmd_str)
        elif cmd == 'DTE':
            dte(user, cmd_str)
        elif cmd == 'AED':
            aed(user, True)
        elif cmd == 'UVF':
            uvf(user, cmd_str)
        elif cmd == 'OUT':
            out(user, clientSocket)
        else:
            print('Error. Invalid command!')

# Server would be running on the same host as Client
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT CLIENT_UDP_PORT======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)
UDP_port = sys.argv[3]

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)

# initiate UDP Server
udpserver(UDP_port)

while True:
    request = {}
    request['action'] = 'login'
    request['user'] = input('Username: ')
    request['psw'] = input('Password: ')
    request['ip_address'] = serverHost
    request['UDP_port_number'] = UDP_port
    clientSocket.sendall(json.dumps(request).encode()) 

    # receive response from the server
    # 1024 is a suggested packet size, you can specify it as 2048 or others
    data = clientSocket.recv(1024)
    login_reply = json.loads(data.decode())
    

    # parse the message received from server and take corresponding actions
    while login_reply['result'] == False:
        if login_reply['msg'] == 'Invalid Password, Please try again.':
            print(login_reply['msg'])
            request['action'] = 'login'
            request['psw'] = input('Password: ')
            clientSocket.sendall(json.dumps(request).encode()) 
    
            data = clientSocket.recv(1024)
            login_reply = json.loads(data.decode())
        elif 'blocked' in login_reply['msg']: 
            print(login_reply['msg'])
            exit(0)
        else:
            print(login_reply['msg'])
    else:
        print(login_reply['msg'])
        run_command(request['user'], clientSocket)

