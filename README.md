# tcp-client-server
 TCP client-server program with P2P exchange over UDP

# Program Design
## Client
Each client runs independently from each other in their own folders simulating file transfer 
over the same separate terminals. The client will establish a TCP connection to the server and 
a UDP server capable of sending and receiving files from other edge devices.
The client should maintain at least two threads while active. One being a thread running the 
TCP connection to the server, processing the commands made to the client by the user. The 
other thread should initiate the UDP server running on the client for P2P communication. 
## Server
The server uses a multi-thread class for the client, where for each connection request by a 
client, a new Thread is created allowing for multi-threading. The class will contain functions 
to login and process each command specified by the edge device. 
The server should retain a record of the failed consecutive login attempts for each edge 
device. When the number of failed attempts equals the servers defined value for unsuccessful 
authentication attempts, the device should be blocked for 10 seconds.
## Trade-offs
I have assumed that during UVF, the video file will transfer completely with no packet loss.
As there is no reliability implemented in UDP, I have added a simple check if the size of the 
file after being transferred by UVF is equal to the expected value.
Similarly, for the sake of simplicity, I have not created a UDP server class for client.py, as
unlike server.py only one other thread is required for receiving UVF and have instead opted 
to use start_new_thread function from _thread
## Improvements & Extensions
I believe I could improve the organisation of the client initialisation and handling of 
authentication to streamline the code and improve readability. Likewise, I would have liked 
to extend the UVF command to correct the output if the client was issuing a command.
Furthermore, I believe the server’s command functions have a high degree of similarity 
between them, which could have been made more efficient and reduced the dependency on 
repeated code.

# System Model
![System Model](https://github.com/pritanb/tcp-client-server/assets/67801415/224dacab-44cc-4009-836f-f7fd04bedbc0)

*Done as part of COMP3331 Computer Networks and Applications 22T3*
