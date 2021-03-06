PK     LJ,J�i��L  L     AddressBook.pyclass AddressBook(dict):
    '''
    A bi-directional dictionary (hash table) used to store username:ip pairs
    and have them be referencable quickly either way. Written by Basj and found
    on StackOverflow at http://stackoverflow.com/a/21894086.
    Modified slightly to improve naming for this particular usage.
    '''
    def __init__(self, *args, **kwargs):
        super(__class__, self).__init__(*args, **kwargs)
        self.byName = {}
        for key, value in self.items():
            self.byName.setdefault(value,[]).append(key) 

    def __setitem__(self, key, value):
        super(__class__, self).__setitem__(key, value)
        self.byName.setdefault(value,[]).append(key)        

    def __delitem__(self, key):
        self.byName.setdefault(self[key],[]).remove(key)
        if self[key] in self.byName and not self.byName[self[key]]: 
            del self.byName[self[key]]
        super(__class__, self).__delitem__(key)


if __name__ == "__main__":
    a = AddressBook()
    a["a"] = 1
    print("a" in a.byName)
    print(a["a"], a.byName[1])PK     N+J�(��B  B     build.pyimport zipfile
from os import walk, path

filelist = []
for (dirpath, dirnames, filenames) in walk(path.dirname(path.realpath(__file__))):
    filelist.extend(filenames)
    break

print(filelist)

with zipfile.ZipFile("build/AlexChat.pyw", "w") as archive:
	for filename in filelist:
		archive.write(filename)PK     
G,J�'��  �     Connection.pyfrom time import sleep
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
            
            
        
PK     �F7JcBH�F  �F     ConnectionManager.pyfrom time import sleep
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
        self.guiQueue.put((self.master.text_received, tabId, msg))PK     �E-J�����
  �
     ConversationTab.pyimport tkinter as tk
from tkinter.scrolledtext import *

class ConversationTab(tk.Frame):
    '''
    This class represents a "tab" in the notebook. It contains the
    GUI elements used to display output to and take input from the user.
    As well as the methods that operate on those elements.
    Inherits from tk.Frame
    '''
    def __init__(self, master, myId):
        super().__init__()
        self.master = master
        self.myId = myId

        self.pack(fill=tk.BOTH, expand=1)
        self.create_widgets()

    def create_widgets(self):
        '''
        This method initializes the GUI elements of the tab,
        such as the "Send" button, the new text entry line, and the
        text display widget.
        '''

        #Display panel for chat history
        self.chatDisplay = ScrolledText(self)
        self.chatDisplay.config(state=tk.DISABLED)
        self.chatDisplay.pack(fill=tk.BOTH, expand=1)

        #Entry line for message to send
        self.lineEntry = tk.Entry(self)                      
        self.lineEntry.bind("<Return>", self.send_message)
        self.lineEntry.pack(fill=tk.BOTH, side=tk.LEFT, expand=1)
        self.lineEntry.focus_set()

        #Send button
        self.entryButton = tk.Button(self, text="Send")
        self.entryButton.bind("<Button-1>", self.send_message)
        self.entryButton.pack(fill=tk.BOTH, side=tk.RIGHT)

    def send_message(self, event):
        '''
        This method reads the text present in the entry box and sends it
        by calling the send_text method of the MainWindow class.
        
        :param event: The event that caused this method to be called.
        '''
        text = str(self.lineEntry.get())
        self.master.send_text(self.myId, text)
        self.lineEntry.delete(0, tk.END)

    def text_received(self, text):
        '''
        This method adds the given text to the text display
        area of the tab. Called by the text_received method of
        the MainWindow class.
        
        :param str text: The text to be added to the display area.
        '''

        #Sent when Connection is closed. At this point, 
        #grey out the entry box and the button to prevent further message sends.
        if text == "<SYSTEM>: CONNECTION CLOSED":
            self.lineEntry.config(state=tk.DISABLED)
            self.entryButton.unbind("<Button-1>")
            self.entryButton.config(state=tk.DISABLED)
            return

        self.chatDisplay.config(state=tk.NORMAL)
        self.chatDisplay.insert(tk.END, text + "\n")
        self.chatDisplay.see(tk.END)
        self.chatDisplay.config(state=tk.DISABLED)
PK     nJ+J��nL  L     CustomNotebook.pyimport tkinter as tk
from tkinter import ttk


class CustomNotebook(ttk.Notebook):
    '''
    A ttk Notebook with close buttons on each tab.
    Written by Bryan Oakley, found at http://stackoverflow.com/a/39459376,
    and modified so that the first two tabs cannot be closed.
    '''

    __initialized = False

    def __init__(self, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._master = args[0]
        
        self._active = None

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button"""

        element = self.identify(event.x, event.y)
        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index

    def on_close_release(self, event):
        """Called when the button is released over the close button"""
        if not self.instate(['pressed']):
            return

        element =  self.identify(event.x, event.y)
        index = self.index("@%d,%d" % (event.x, event.y))

        #Edited to prevent deletion of first 2 tabs
        #Overview and Broadcast
        if "close" in element and self._active == index and self._active > 1:
            #Added to notify MainWindow of tab close
            self.master.tab_closed(self.tab(self._active, "text").split()[0]) 
            
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")

        self.state(["!pressed"])
        self._active = None

    '''def add(self, tab, text="Dafault text", isCloseable=True):
        if not isClosable:
            self.nonClosable.append()'''
        

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                '''),
            tk.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                '''),
            tk.PhotoImage("img_closepressed", data='''
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            ''')
        )

        style.element_create("close", "image", "img_close",
                            ("active", "pressed", "!disabled", "img_closepressed"),
                            ("active", "!disabled", "img_closeactive"), border=8, sticky='')
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe", 
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top", 
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top", 
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),
                                ]
                        })
                    ]
                })
            ]
        })
    ])

if __name__ == "__main__":
    root = tk.Tk()

    notebook = CustomNotebook(width=200, height=200)
    notebook.pack(side="top", fill="both", expand=True)

    for color in ("red", "orange", "green", "blue", "violet"):
        frame = tk.Frame(notebook, background=color)
        notebook.add(frame, text=color)

    root.mainloop()
PK     
G,J���*  *     MainWindow.pyimport tkinter as tk
from tkinter import ttk

import CustomNotebook
import ConversationTab
import ConnectionManager
import queue, sys

class MainWindow(tk.Frame):
    '''
    The root class in the application, contains all objects. Handles the basic
    GUI layout, as well as passing messages between the network code (NetworkManager)
    and the ConversationTabs where input is taken and output is displayed.
    Inherits from tkinter.Frame.
    '''
    def __init__(self, master):
        '''
        The class constructor for MainWindow. Sets up the basic structure of the window.
        
        :param master: The master is the basic tkinter window object (Tk.tk()).
        '''
        super().__init__()

        self.master = master
        self.master.wm_title("AlexChat")

        #Call self.on_close when the user clicks the 'X' button on the window
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tabs = {} #id:Conversationtab(self, idOfTab)
        self.pack(fill=tk.BOTH, expand=1)
        
        #Initialize basic GUI elements.
        self.create_widgets()

        #ConnectionManager handles all network code in separate threads
        #needed because tkinter methods cannot be called from any thread but the main one
        #instead, functions and args are passed using the queue, and executed in main thread
        self.instructionQueue = queue.Queue()
        self.manager = ConnectionManager.ConnectionManager(self, self.instructionQueue)
        self.queue_loop()

    def create_widgets(self):
        '''
        Method to initialize default GUI elements, namely the Notebook and the Overview tab.
        '''
        #Tabbed view, each tab is a conversation
        self.tabbed = CustomNotebook.CustomNotebook(self)
        self.tabbed.pack(fill=tk.BOTH, expand=1)

        #Overview tab shows connection data, is where you input your username
        self.tabs["Overview"] = ConversationTab.ConversationTab(self, "Overview")
        self.tabbed.add(self.tabs["Overview"], text="Overview")

    def queue_loop(self):
        '''
        A looping method to handle function calls passed from the network manager
        via the instructionQueue. Repeats every 250ms. Used to placate tkinter's hatred of threads
        '''
        while not self.instructionQueue.empty():
            i = self.instructionQueue.get()
            function = i[0]
            args = i[1:]
            function(*args) #Executes specified function with specified args
        self.after(250, self.queue_loop) #Repeat function after specified number of milliseconds

    def add_tab(self, newId):
        '''
        A method that adds a tab with the given ID. The ID is also the title.
        
        :param str newId: The ID of the new tab
        '''
        self.tabs[newId] = ConversationTab.ConversationTab(self, newId)
        self.tabbed.add(self.tabs[newId], text=newId)

    def text_received(self, thisId, text):
        '''
        A method to add a given string to the ConversationTab with the given ID.        

        :param str thisId: The ID of the tab where the message should be sent.
        :param str text: The text to be added to the tab. 
        '''
        if thisId in self.tabs:
            self.tabs[thisId].text_received(text)

    def send_text(self, thisId, text):
        '''
        A method called by ConversationTabs to send the
        given text to the NetworkManager to be sent.
        
        :param str thisId: The ID of the tab sending the message
        :param str text: The text to be sent.
        '''
        self.manager.new_write(thisId, text)

    def tab_closed(self, tabId):
        '''
        A method called by the CustomNotebook when a tab is
        closed by pressing the 'X' button.

        :param str tabId: The ID of the tab to be closed.
        '''
        self.manager.delete_connection(tabId)

    def on_close(self):
        '''
        A method called when the root window is closed. Signals the
        NetworkManager to close all connections, then closes the window.
        '''
        self.manager.close_all()
        self.master.destroy()
        sys.exit(0)
           
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    app.mainloop()PK     F-J�@b�  �     MySocket.pyclass MySocket(object):
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
        passPK     �F7J΋L��  �     TCPSocket.pyimport socket
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
    
PK     �F7J;YQ�c	  c	     UDPSocket.pyimport socket
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

    
PK     QkIC��s   s      __main__.pyimport tkinter as tk
from MainWindow import MainWindow

root = tk.Tk()
app = MainWindow(root)
app.mainloop()
PK      LJ,J�i��L  L             ��    AddressBook.pyPK      N+J�(��B  B             ��x  build.pyPK      
G,J�'��  �             ���  Connection.pyPK      �F7JcBH�F  �F             ���  ConnectionManager.pyPK      �E-J�����
  �
             ���Z  ConversationTab.pyPK      nJ+J��nL  L             ���e  CustomNotebook.pyPK      
G,J���*  *             ��:w  MainWindow.pyPK      F-J�@b�  �             ����  MySocket.pyPK      �F7J΋L��  �             ��\�  TCPSocket.pyPK      �F7J;YQ�c	  c	             ��J�  UDPSocket.pyPK      QkIC��s   s              ��ע  __main__.pyPK      �  s�    