import tkinter as tk
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
    app.mainloop()