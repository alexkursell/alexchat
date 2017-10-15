import tkinter as tk
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
