"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: Pritan Barai 
    - Code referenced from RUI LI assignment demos
"""
import os
from socket import *
from statistics import mean
from threading import Thread
from collections import defaultdict
import sys
import select
from datetime import datetime, timedelta
import json

# acquire server host and port from command line parameter
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT NUM_FAILED_ATTEMPTS =====\n")
    exit(0)
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# acquire number_of_consecutive_failed_attempts from command line parameter
serverFailedAttempts = int(sys.argv[2])
if not 1 <= serverFailedAttempts <= 5:
    print(
        f"\n===== Invalid number of allowed failed consecutive attempts: {serverFailedAttempts}. The valid value of argument number is an integer between 1 and 5 =====\n")
    exit(0)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

# define dictionaries for user failed login attempts and blocked users
login_failed_times = defaultdict(int)
login_block = defaultdict(lambda: datetime.min)

# active users dictionary
active_users = []

# define path
path = f'{os.getcwd()}/'

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be running in a separate thread, which is the multi-threading
"""
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False

        print("===== New connection created for: ", clientAddress)
        self.clientAlive = True

    def run(self):
        message = ''
        global login_failed_times
        global login_block
        global active_users

        while self.clientAlive:
            # use recv() to receive message from the client
            data = self.clientSocket.recv(1024)
            message = data.decode()
            client_request = json.loads(message)
            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if not client_request:
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break

            # handle message from the client
            if client_request['action'] == 'login':
                print("[recv] New login request")
                self.process_login(client_request)
            elif client_request['action'] == 'UED':
                print("[recv] UED request")
                self.process_ued(client_request)
            elif client_request['action'] == 'SCS':
                print("[recv] SCS request")
                self.process_scs(client_request)
            elif client_request['action'] == 'DTE':
                print("[recv] DTE request")
                self.process_dte(client_request)
            elif client_request['action'] == 'AED':
                print("[recv] AED request")
                self.process_aed(client_request)
            elif client_request['action'] == 'OUT':
                print("[recv] OUT request")
                self.process_out(client_request)
                return


    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """

    def process_login(self, client_request):
        # load credentials from file into dictionary
        credentials = {}
        with open("credentials.txt") as c:
            for line in c:
                (c_user, c_pass) = line.strip().split(' ')
                credentials[c_user] = c_pass

        username = client_request['user']
        psw = client_request['psw']
        client_ip_address = client_request['ip_address']
        client_UDP_port = client_request['UDP_port_number']

        reply = {}
        if (username, psw) in credentials.items():
            curr_time = datetime.now()
            if curr_time < login_block[username]:
                reply['result'] = False
                reply['msg'] = 'Your account is blocked due to multiple authentication failures. Please try again later'
            else:
                active_users.append(username)
                seq_number = active_users.index(username) + 1
                with open("edge-device-log.txt", "a+") as edge_device_log:
                    edge_device_log.write(f'{seq_number}; {curr_time.strftime("%d %B %Y %H:%M:%S")}; {username}; {client_ip_address}; {client_UDP_port}\n')

                reply['result'] = True
                reply['msg'] = 'Welcome!'
        else:
            # record for failed logins
            login_failed_times[username] += 1
            if login_failed_times[username] < serverFailedAttempts:
                reply['result'] = False
                reply['msg'] = 'Invalid Password, Please try again.'
                print(
                    f"user: {username} failed {login_failed_times[username]} times")
            else:
                curr_time = datetime.now()
                login_block[username] = curr_time + timedelta(seconds=10)
                # user is blocked so failed attempts resets
                login_failed_times[username] = 0
                reply['result'] = False
                reply['msg'] = 'Invalid Password. Your account has been blocked. Please try again later'

        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())

    def process_ued(self, client_request):
        user = client_request['user']
        data = client_request['data']
        file_id = client_request['file_id']
        data_amount = client_request['data_amount']

        reply = {}

        try:
            with open(f"{user}-{file_id}.txt", "w+") as file:
                file.write(data)
            reply['msg'] = f"Data file with ID of {file_id} has been uploaded to server"
        except:
            reply['msg'] = 'File transfer unsuccessful'


        with open("upload-log.txt", "a+") as upload_log:
            curr_time = datetime.now()
            upload_log.write(f'{user}; {curr_time.strftime("%d %B %Y %H:%M:%S")}; {file_id}; {data_amount}\n')
        
        
        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())

    def process_scs(self, client_request):
        user = client_request['user']
        file_id = client_request['file_id']
        operation = client_request['operation']

        reply = {}

        filename = f'{user}-{file_id}.txt'
        if not os.path.isfile(path + filename):
            reply['msg'] = 'the file does not exist at the server side'

        # Convert data sample to array
        data = []
        with open(filename, "r") as file:
            for line in file:
                data.append(int(line.strip()))

        result = 0
        if operation == 'SUM':
            result = sum(data)
        elif operation == 'MAX':
            result = max(data)
        elif operation == 'MIN':
            result = min(data)
        elif operation == 'AVERAGE':
            result = mean(data)
        else:
            reply['msg'] = 'Invalid Operation'

        reply['msg'] = f'Computation {operation} result on the file {file_id} returned from the server is: {result}'
        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())

    def process_dte(self, client_request):
        user = client_request['user']
        file_id = client_request['file_id']
        data_amount = client_request['data_amount']

        reply = {}

        filename = f'{user}-{file_id}.txt'
        if os.path.isfile(path + filename):
            os.remove(path + filename)
            with open("deletion-log.txt", "a+") as deletion_log:
                curr_time = datetime.now()
                deletion_log.write(f'{user}; {curr_time.strftime("%d %B %Y %H:%M:%S")}; {file_id}; {data_amount}\n')
            reply['msg'] = f'The file with ID of {file_id} from edge device {user} has been deleted, deletion log file has been updated'
        else:
            reply['msg'] = 'the file does not exist at the server side'

        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())

    def process_aed(self, client_request):
        user = client_request['user']

        reply = {}
        active_edge_devices = ""

        with open("edge-device-log.txt", "r") as edge_device_log:
            for line in edge_device_log:
                seq_number, timestamp, username, ip_address, UDP_port_number = line.split("; ")
                if username != user:
                    active_edge_devices += f'{username}; {ip_address}; {UDP_port_number.strip()}; active since {timestamp}.\n'

        if active_edge_devices == "":
            reply['msg'] = 'no other active edge devices'
        else:
            reply['msg'] = active_edge_devices.strip()

        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())

    def process_out(self, client_request):
        user = client_request['user']

        new_log = []
        with open("edge-device-log.txt", "r") as log:
            for line in log:
                seq_number, timestamp, username, ip_address, UDP_port_number = line.split("; ")
                if username == user:
                    active_users.remove(username)
                else:
                    seq_number = active_users.index(username) + 1
                    new_log.append(f'{seq_number}; {timestamp}; {username}; {ip_address}; {UDP_port_number}')

        with open("edge-device-log.txt", "w") as log:
            for entry in new_log:
                log.write(entry)
  
        reply = {}
        reply['msg'] = f"Bye, {user}!"     
        
        print('[send] ' + reply['msg'])
        self.clientSocket.send(json.dumps(reply).encode())       

print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
