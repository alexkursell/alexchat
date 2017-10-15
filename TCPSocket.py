import socket
from time import sleep
from MySocket import MySocket
class TCPSocket(MySocket):
    '''
    A class that represents a TCP connection with a specified host.
    Wraps around an actual socket.socket, and implements send and receive methods
    for easier usage.
    '''
    def __init__(self, ip, port=None):
        '''
        Class constructor. Takes either a socket.socket or an IP address and
        port number and initializes the TCPSocket. If it receives an IP and port,
        this method is also where the socket.socket is created and connected.
        
        :param ip: If port is specified, ip is an IP address\
        if port is not specified, ip is a socket.socket object.
        :param int port: The port number on the host to be connected to.
        '''

        #Used to prevent socket close with data still to be written.
        self.dataBeingSent = False

        if port == None:
            self.sock = ip
        else:
            self.ip = ip
            self.port = port
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))

    def send(self, msg):
        '''
        A method that sends a message through the socket.
        
        :param str msg: The message to be sent.
        '''
        self.dataBeingSent = True

        try:
            #Encode message to be sent as UTF-8 with ASCII EOT terminator.
            msg = bytearray(msg.encode())
            msg.append(ord('\x04'))  #ASCII EOT byte
            msg = bytes(msg)

            #Send packets until whole message is sent.
            totalsent = 0
            while totalsent < len(msg):
                try:
                    sent = self.sock.send(msg[totalsent:])
                except ConnectionResetError:
                    self.dataBeingSent = False
                    raise

                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent

        except:
            raise RuntimeError("Send message failed.")
        finally:
            self.dataBeingSent = False
    
    def receive(self):
        '''
        A method that waits until it receives a message and returns that message,
        along with the IP address of the sender.
        
        :rtype: tuple
        '''
        chunks = []
        while True:
            chunk = self.sock.recv(2048)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            
            if chr(chunk[-1]) == '\x04': #ASCII EOT byte
                break
        #Returns (message, ip of sender)
        return (str(b''.join(chunks)[:-1])[2:-1].replace("\\n", "\n").rstrip(), self.sock.getpeername()[0])


if __name__ == "__main__":
    s = MySocket()
    s.sock.settimeout(0.25)
    print(s.try_connect('10.243.67.97', 1298))
    
