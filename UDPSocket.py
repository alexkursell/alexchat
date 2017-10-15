import socket
from MySocket import MySocket
class UDPSocket(MySocket):
    '''
    A class that represents a UDP broadcast connection.
    Wraps around an actual socket.socket, and implements send and
    receive methods for easier usage. This class is used to broadcast a message
    to all hosts on the network simultaneously, using the UDP broadcast feature.
    '''
    def __init__(self, thisHost, port=1298):
        '''
        Class constructor. Takes an IP address (of this host) and optionally
        the number of the port to send and receive on.

        :param str thisHost: The IP address of this computer.
        :param int port: The port to send and receive messages on.
        '''

        #Used to prevent socket close with data still to be written.
        self.dataBeingSent = False

        self.thisHost = thisHost #Needed to prevent receiving our own messages
        self.port = port
        
        #Set up the socket as a UDP broadcast socket.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port))

    def send(self, msg):
        '''
        A method that sends a message through the socket. Sends only
        a single packet, so message length must be limited.
        
        :param str msg: The message to be sent.
        '''
        
        self.dataBeingSent = True
        try:
            if msg == "":
                return
            msg = bytes(msg.encode())
            sent = self.sock.sendto(msg, ('<broadcast>', self.port))
            if sent == 0:
                raise RuntimeError("socket connection broken")
        except:
            pass
        finally:
            self.dataBeingSent = False

    def receive(self):
        '''
        A method that waits untill it receives a message and returns that message,
        along with the IP address of the sender.
        
        :rtype: tuple
        '''
        while True:
            chunk = self.sock.recvfrom(2048)
            if chunk[1][0] != self.thisHost: #Only return message if it wasn't send by this host
                #Return (message, ip of sender)
                return (str(chunk[0])[2:-1], chunk[1][0])

    
