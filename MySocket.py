class MySocket(object):
    '''
    Base class for my socket objects, TCPSocket and UDPSocket. Adds
    ability to be used as an iterable. (implements __enter__, __exit__, __iter__, and __next__)
    '''
    def __enter__(self):
        pass
    
    def __exit__(self, type, value, traceback):
        #Return true means that any exception encountered when using the 'with'
        #statement is not raised, the program just moves to whatever is after the 'with'
        #block. Used because I don't care exactly how a socket died, when it dies I just
        #need to state that the connection is closed and end the read loop.
        return True
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return self.receive()
    
    def close(self): 
        '''
        A method that closes the socket. Waits until data is not being sent.
        '''
        while self.dataBeingSent:
            sleep(0.1)

        self.sock.close()

    def send(self, msg):
        '''Overloaded by TCPSocket and UDPSocket'''
        pass
    
    def receive(self):
        '''Overloaded by TCPSocket and UDPSocket'''
        pass