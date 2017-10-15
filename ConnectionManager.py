from time import sleep
import socket
import threading
import sys
import queue
from Connection import Connection
from TCPSocket import TCPSocket
from UDPSocket import UDPSocket
from AddressBook import AddressBook


class ConnectionManager():
    '''
    The class that creates and manages all network Connections.
    Handles message routing reading and writing to MainWindow,
    user command handling, creating, listening for, and closing connections,
    storing usernames and ip addresses.
    '''
    def __init__(self, master, guiQueue):
        '''
        The class constructor for ConnectionManager. Sets up socket server,
        broadcasting, and runs session_setup
        
        :param MainWindow master: The master is the MainWindow object to send and receive messages with.
        :param Queue guiQueue: The queue to write commands for the GUI code to.
        '''
        self.guiQueue = guiQueue
        self.master = master
        self.host = self.get_hostname()
        self.port = 1298 #TCP and UDP server port.
        self.username = ""


        self.userList = AddressBook()
        self.connections = {}

        self.helpString = '''Available commands:
            /help - Displays help information.
            /ip - Displays ip address of this computer.
            /join <username or ip> - Connects to specified username or ip.
            /list - Shows a list of available users.
            /quit - Ends current chat.
            '''
        
        #Create socket to listen for incoming connections
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((self.host, self.port))
        self.serverSocket.listen(5)

        #Open broadcast socket and start listening.
        self.connections["Broadcast"] = Connection("Broadcast",
                                                   UDPSocket(self.host, self.port),
                                                   self)
        self.connections["Broadcast"].start_listening()

        #Begin session setup
        self.listenerThread = threading.Thread(target=self.session_setup)
        self.listenerThread.start()

    def get_hostname(self):
        '''
        A method that returns the ip address of the computer.
        Works by creating a temporary UDP connection to Google (but since it's UDP
        it won't actually send anything), then reading the IP of the connection.

        :rtype: str
        '''

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1)) #Dosen't have to be reachable.
        return s.getsockname()[0]

    def session_setup(self):
        '''
        A method called by the constructor that prompts for a username,
        then once one is entered, calls listen_for_connections to
        start accepting connections.
        '''
        self.log("Getting all users on network...")

        #Send /REQUEST signal to get list of usernames
        self.connections["Broadcast"].send("/REQUEST " + self.username)
        sleep(5)
        self.log("Done.")

        while True:
            self.log("Enter a username, no periods or spaces:")

            #Wait for username to be input.
            while self.username == "":
                sleep(0.25)

            self.log("Checking for username conflicts...")

            if self.username not in self.userList.byName:
                self.log("No username conflict detected.")
                break
            
            self.log("Username conflict detected. Choose another name:")
            self.username = ""
        
        #Announce username to the world.
        self.connections["Broadcast"].send("/USRADD " + self.username)
        
        #Display welcome messages.
        self.log("Welcome, " + self.username + ".")
        self.log("Type '/help' for a list of available commands.")

        #Add my new username to the directory.
        self.userList[self.host] = self.username

        #Open a tab to display output of the Broadcast socket
        self.guiQueue.put((self.master.add_tab, "Broadcast"))

        #Listen for incoming connections
        self.listen_for_connections()

    def do_handshake(self, newConnection):
        '''
        A method called when a new connection (outbound
        or inbound) is being created. Sends a '/HANDSHAKE' command
        followed by the username of this computer, then waits for
        and returns the username of the new client.

        :param Connection newConnection: The new connection to perform the handshake on.
        :rtype: str
        '''
        newConnection.send("/HANDSHAKE " + self.username)
        while True:
            r = newConnection.receive()[0].split()
            newConnection.set_id(r[1])
            if r[0] == "/HANDSHAKE":
                return r[1]
        
    def listen_for_connections(self):
        '''
        A method containing an infinite loop that listens for
        incoming socket connections. When one is detected, it creates a new
        Connection, performs the handshake, and then adds the Connection and
        creates a new GUI tab for the chat.
        '''
        self.log('Listening for connections...')
        while True:
            try:
                #Accept a new incoming connection
                (clientsocket, address) = self.serverSocket.accept()
            except OSError:
                #Program is being shut down, end loop
                return None

            
            self.log('New incoming connection from %s:%i' % (address[0], address[1]))

            #Create a new TCPSocket and Connection object with the returned socket
            newConnection = Connection(address, TCPSocket(clientsocket), self)

            #Get the nickname of the other person.
            try:
                nickname = self.do_handshake(newConnection)
            except:
                self.log("Incoming connection add failed.")
                continue
            
            self.connections[nickname] = newConnection

            #Start listening through the connection
            newConnection.start_listening()

            #Add a tab to the GUI
            self.guiQueue.put((self.master.add_tab, nickname))
            self.log('%s:%i (%s) connected.' % (address[0], address[1], nickname))

    def add_connection(self, ip, logId="Overview"):
        '''
        A method that connects with the given host on the given port.
        It creates a new Connection, performs the handshake, then adds the Connection
        and creates a new GUI tab.
        
        :param str ip: The ipv4 address or username of the computer to connect to.
        :param int port: The port to try connecting to.
        :param str logId: The default tab to log status of connection add to.
        '''
        
        self.log("Attempting to add connection with " + ip + "...", logId)
        
        #Prevent creation of duplicate connections
        if ip in self.connections:
            self.log("Connection already exists.", logId)
            return None


        if "." not in ip: #Without a dot assume ip is a username
            if ip in self.userList.byName:
                name = ip
                ip = self.userList.byName[name][0]

                self.log("%s found at %s." % (name, ip), logId)
            else:
                self.log(
                    "%s is not a known user or correctly formatted IP address, please try again."
                    % (ip), logId)
                return None
        else:
            name = ip
            

        self.log("Adding new connection with %s:%i..." % (ip, self.port), logId)

        try:
            newConnection = Connection(name, TCPSocket(ip, self.port), self)
            name = self.do_handshake(newConnection)
        except:
            self.log("Connection open failed.", logId)
            return
        
        self.connections[name] = newConnection
        newConnection.start_listening()


        self.guiQueue.put((self.master.add_tab, name))
        self.log('%s:%i (%s) connected.' % (ip, self.port, name), logId)
        
    def receive_command(self, thisId, commands):
        '''
        A method used to switch commands sent through a Connection by the other party.
        
        :param str thisId: The ID of the Connection that receives the command.
        :param tuple commands: A tuple containing the received command and \
        the other party's IP address.
        '''
        ip = commands[1]
        commands = commands[0]

        
        for command in commands.split("\n"):
            command = command.split()

            #Sent by new users and by all users whenever
            #a new user starts the program
            if command[0] == "/USRADD":
                #If the new username is the same as this one, send a
                #NAMECONFLICT, otherwise, add the user.
                if self.username == command[1]:
                    self.connections["Broadcast"].send("/NAMECONFLICT "
                                                      + self.username)
                else:
                    self.add_user((command[1], ip))

            #A smiple request for all users on the network to send their names
            elif command[0] == "/REQUEST":
                if self.username != "":
                    self.connections["Broadcast"].send("/USRADD "
                                                        + self.username)
                
            #If this is recieved, the chosen name is conflicted, so remove it.
            elif command[0] == "/NAMECONFLICT":
                if command[1] == self.username:
                    self.username = ""
                else:
                    self.add_user((command[1], ip))
                
            #Sent whenever a user ends a chat or goes offline. In the first case,
            #end the chat on this end, in the second, delete the user from memory.
            elif command[0] == "/DISCONNECT":
                if thisId != "Broadcast":
                    self.log("Connection with %s closed by partner." % thisId)
                    self.log("Connection closed by partner.", thisId)
                    self.delete_connection(thisId)
                else:
                    self.delete_user(ip)
                    
    def handle_command(self, thisId, command):
        '''
        A method used to switch commands typed into the GUI by the user.
        A command is preceded by a forward slash '/'.
        
        :param str thisId: The ID of the tab that sent the command.
        :param str command: The text of the command.
        '''

        command = command.split()
        command[0] = command[0].lower()

        #/quit command quits the current chat
        if command[0] == "/quit":
            if thisId in ["Broadcast", "Overview"]:
                self.log("The %s tab is always open." % thisId, thisId)
            elif thisId in self.connections:
                self.delete_connection(thisId)
                self.log("Connection with %s closed." % thisId)
                self.log("Connection closed.", thisId)
            else:
                self.log("Connection already closed.", thisId)

        #Try to add connection to specified user
        elif command[0] == "/join":
            if len(command) == 1:
                self.log("No username or IP specified.", thisId)
            elif command[1] == self.username:
                self.log("You can't chat with yourself!", thisId)
            else:
                self.add_connection(command[1], thisId)
       
        #Display the help string.
        elif command[0] == "/help":
            self.log(self.helpString, thisId)

        #Display my ip
        elif command[0] == "/ip":
            self.log("Your IP address is " + str(self.host), thisId)

        #Display a list of all known users
        elif command[0] == "/list":
            self.log("Users:\n" + "\n".join(
                [(" " * 12) + "{:17} {}".format(name, ip)\
                 for (ip, name) in self.userList.items()]), thisId)
        else:
            self.log("Command not found.", thisId)


    def add_user(self, items):
        '''
        A method that adds the given user to memory
        (or updates an existing user).

        :param items: The username and IP, format (username, ip).
        :type items: tuple or list
        '''
        self.userList[items[1]] = items[0]

    def delete_user(self, ip):
        '''
        A method that deletes the user entry for the user with
        a given IP address.
        
        :param str ip: The IP address of the user to be deleted.
        '''
        del self.userList[ip]
        
    def delete_connection(self, thisId):
        '''
        A method that closes and deletes the Connection with the
        given ID.
        
        :param str thisId: The ID of the Connection to be closed.
        '''
        #Send a DISCONNECT then close connection and delete from memory.
        try:
            self.connections[thisId].send("/DISCONNECT " + self.username)
            self.log("Connection with %s closed." % (thisId))
        
            self.connections[thisId].close()
            del self.connections[thisId]

        #This procedure can throw a lot of errors under different circumstances
        except KeyError:
            return
        except ConnectionResetError:
            pass
        except ConnectionAbortedError:
            pass
        
    def new_read(self, thisId, msg):
        '''
        A method called by a Connection to when a message is received. If message is a command
        (starts with '/'), it calls the command handler, otherwise it displays
        the text of the message with a tag containing either the username
        associated with the client IP, or just with the client IP (if for some reason
        no username is available).
        
        
        :param str thisId: The ID of the tab to display the message on.
        :param tuple msg: The text of the message and the IP of the sender, format (text, ip).
        '''

        #'/' denotes a command to be handled
        if msg[0].startswith("/"):
            self.receive_command(thisId, msg)
        else:
            #Replace the IP address sent by the Connection with the username
            #stored for that address. Display message.
            if msg[1] in self.userList.keys():
                self.guiQueue.put((self.master.text_received, thisId,
                                   "<" + self.userList[msg[1]] + ">: " + msg[0]))
            else:
                self.guiQueue.put((self.master.text_received, thisId,
                                   "<" + msg[1] + ">: " + msg[0]))
            
    def new_write(self, thisId, msg):
        '''
        A method called by the MainWindow when a new message needs to be sent
        (or a command is entered). This method switches commands and messages and
        does the appropriate thing for each.
        
        :param str thisId: The ID of the tab that sent the message (as well as of the Connection)
        :param str msg: The message to be sent, or command to be executed.
        '''

        #Empty means no username, program is in setup, entered command is actually username
        #that the user wants to select.
        if self.username == "":
            if " " in msg or "." in msg or "/" in msg:
                self.log("Sorry, no periods, slashes, or spaces allowed. Enter another username.")
            elif len(msg) > 16:
                self.log("Maximum username length (16) exceeded. Enter another username.")
            elif msg in self.userList.keys():
                self.log("Sorry, this username is already in use. Enter another username.")
            elif msg.lower() in ["me", "system"]:
                self.log("Think we're clever, do we? Try again buddy.")
            else:
                self.username = msg


        elif msg.startswith("/"):
            self.handle_command(thisId, msg)
        elif len(msg) > 1000:
            self.log("Message too long. Maximum size is 1000 characters.", thisId)
        elif thisId == "Overview":
            self.handle_command(thisId, "/" + msg)
        else:
            self.connections[thisId].send(msg)
            self.log("<me>: " + msg, thisId)

    def close_all(self):
        '''
        A method that closes and deletes every connection.
        Called on program shutdown. Does not use delete_connection
        method because a pause is required between sending the signal
        and closing the socket, so it is more efficient to sent all signals, wait,
        then close all sockets.
        '''

        self.serverSocket.close()
        idList = list(self.connections.keys())

        #Send DISCONNECT to every connection
        for x in idList:
            try:
                self.connections[x].send("/DISCONNECT " + self.username)
            except KeyError:
                pass

        sleep(0.1)

        #Close every connection
        for x in idList:
            try:
                self.connections[x].close()
                del self.connections[x]
            except KeyError:
                pass

    def log(self, msg, tabId="Overview"):
        '''
        A method that writes text to the specified tab, without appending a username
        or ip. Default tab to write logging data to is Overview.
        
        :param str msg: The text of the message to be displayed.
        :param str tabId: The ID of the tab that will display the message.
        '''
        self.guiQueue.put((self.master.text_received, tabId, msg))