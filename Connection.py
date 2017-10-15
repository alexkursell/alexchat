from time import sleep
import threading

class Connection():
    '''
    This class provides a convenient layer between the NetworkManager
    and a socket object (either UDPSocket or TCPSocket), allowing messages
    from the socket to be read and sent to the proper method of the ConnectionManager class.
    '''
    def __init__(self, myId, sock, master=None):
        '''
        The constructor for Connection. Stores some basic
        information including the socket object and the ID.
        
        :param str myId: The ID of this connection.
        :param sock: The socket object to be used.
        :param master: The ConnectionManager who's methods should be called.
        '''
        self.myId = myId
        self.sock = sock
        self.master = master

    def start_listening(self):
        '''
        Create and start a thread to continuously read for input
        from the socket.
        '''
        self.receiverThread = threading.Thread(target=self.read_loop)
        self.receiverThread.start()

    def read_loop(self):
        '''
        Contains an infinite loop that waits for input from the socket
        and passes it to the new_read method in the ConnectionManager.
        '''

        #The 'with' statement automatically calls the __enter__ method when
        #entering the block, and calls the __exit__ method when exiting the block
        with self.sock:
            #By adding the __iter__ and __next__ methods to MySocket, it becomes
            #iterable, where each iteration returns the next message received, and
            #if there is none, waits until it becomes available.
            for msg in self.sock:
                if self.master == None:
                    print(msg)
                else:
                    self.master.new_read(self.myId, msg)

        #Socket has died or closed, announce that it has closed, and end reading.
        self.master.new_read(self.myId, ("CONNECTION CLOSED", "SYSTEM"))


    def write_loop(self):
        '''
        An infinite loop that waits for user input and writes it to the socket.

        .. warning:: Not used by ConnectionManager, since it blocks it should \
        only be run when the Connection is being used as a stand-alone program.
        '''
        while True:
            i = input()
            if i == "":
                break
            self.sock.send(i)
            sleep(0.5)

    def send(self, msg):
        '''
        A method that sends a message through the socket.
        
        :param str msg: The message to be sent.
        '''
        try:
            self.sock.send(msg)
        except RuntimeError:
            pass

    def receive(self):
        '''
        A method that waits untill it receives a message
        from the socket, then returns that message, as well as the senders IP.
        
        :rtype: tuple
        '''
        return self.sock.receive()

    def close(self):
        '''
        A method that closes the socket.
        '''
        self.sock.close()

    def set_id(self, newId):
        '''
        A method that sets the ID of the socket. It often needs to be changed
        once a username is received (as the ID is the connected username).
        
        :param str newId: The new ID.
        '''
        self.myId = newId


if __name__ == "__main__":
    c = Connection("0", UDPSocket(1298))
    c.start_listening()
    c.write_loop()
            
            
        
