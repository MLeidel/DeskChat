# convmgr.py
# conversations manager
# TODO
#

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
from pathlib import Path
import json
import platform
import os # Added for path handling
import sys
import shutil
import configparser
import subprocess
from time import localtime, strftime
from ttkbootstrap import *
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import ToolTip

if platform.system() == "Windows":
    histfile = str(Path("C:\\", "DeskChat", "convhist", "default.json"))
else:
    histfile = "./convhist/default.json"

class conversManagerApp(Tk):
    '''
        The app saves live conversation.json files for later recall and further discussion.
        It documents and dates them lists them for selection and management.
        This app is built to work with DeskChat.
    '''
    def __init__(self):
        super().__init__() # call Tk's constructor
        self.title("Conversations Manager")
        self.protocol("WM_DELETE_WINDOW", self.save_location)  # UNCOMMENT TO SAVE GEOMETRY INFO
        # Window Metrics
        if os.path.isfile("promet"):
            with open("promet") as f:
                lcoor = f.read()
            self.geometry(lcoor.strip())
        else:
            self.geometry("800x600") # WxH+left+top

        config = configparser.ConfigParser()
        config.read('options.ini')
        MyTheme = config['Main']['theme']
        self.MyEditor = config['Main']['editor']

        style = Style()
        style = Style(theme=MyTheme)

        self.conversations = []
        self.current_file = None

        self._create_widgets()
        self._layout_widgets()
        self.load_conversations() # Load conversations on startup

        # Add menu bar
        self._create_menu()

        # Add event bindings for Treeview selection
        self.convers_tree.bind("<<TreeviewSelect>>", self.select_conversation)

    def _create_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_conversations)
        file_menu.add_command(label="Save As...", command=self.save_conversations_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

    def _create_widgets(self):
        # Input Frame
        self.input_frame = Frame(self)
        Label(self.input_frame, text="Conversation:").grid(row=0, column=0, sticky="e", pady=2)
        self.name_entry = Entry(self.input_frame, width=50, font=('Arial', 12, 'bold'))
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=5)

        Label(self.input_frame, text="Description:").grid(row=1, column=0, sticky="ne", pady=2)
        self.text_entry = Text(self.input_frame, width=50, height=10)
        self.text_entry.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        efont = Font(family="Mono", size=11)
        self.text_entry.config(wrap="word",
                                font=efont,
                                undo=True,
                                padx=5,
                                tabs=(efont.measure(' ' * 4),))
        Label(self.input_frame, text="Tags:").grid(row=2, column=0, sticky="e", pady=2)
        self.tags_entry = Entry(self.input_frame, width=50, font=('Arial', 12, 'bold'))
        self.tags_entry.grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        ToolTip(self.tags_entry,
                text="Comma Separated Tags",
                bootstyle=("inverse-secondary"),
                wraplength=140)

        # Buttons Frame
        self.button_frame = Frame(self.input_frame)
        self.add_button = Button(self.button_frame, text="Add Conv", command=self.add_convers)
        ToolTip(self.add_button,
                text="Save the current live conversatioin",
                bootstyle=("inverse-secondary"),
                wraplength=140)
        self.update_button = Button(self.button_frame, text="Update Conv", command=self.update_convers)
        ToolTip(self.update_button,
                text="Change description and tags for a saved conversation",
                bootstyle=("inverse-secondary"),
                wraplength=140)
        self.delete_button = Button(self.button_frame, text="Delete Conv", command=self.delete_convers)
        ToolTip(self.delete_button,
                text="Remove a saved conversation",
                bootstyle=("inverse-secondary"),
                wraplength=140)
        self.view_button = Button(self.button_frame, text="View", command=self.view_selected)
        ToolTip(self.view_button,
                text="View the json for the selected conversation",
                bootstyle=("inverse-secondary"),
                wraplength=140)
        self.copy_button = Button(self.button_frame, text="Make Live", command=self.copy_conversation)
        ToolTip(self.copy_button,
                text="Restart a saved conversation to bring it live.",
                bootstyle=("inverse-secondary"),
                wraplength=140)
        self.add_button.pack(side="left", padx=5)
        self.update_button.pack(side="left", padx=5)
        self.delete_button.pack(side="left", padx=5)
        self.view_button.pack(side="left", padx=5)
        self.copy_button.pack(side="left", padx=5)

        self.button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        # convers List Frame
        self.list_frame = Frame(self)
        self.convers_tree = ttk.Treeview(self.list_frame, columns=("Name", "Tags"), show="headings")
        self.convers_tree.heading("Name", text="Saved Conversations")
        self.convers_tree.heading("Tags", text="Tags")
        self.convers_tree.column("Name", width=200)
        self.convers_tree.column("Tags", width=150)

        self.tree_scrollbar_y = Scrollbar(self.list_frame, orient="vertical", command=self.convers_tree.yview)
        self.tree_scrollbar_x = Scrollbar(self.list_frame, orient="horizontal", command=self.convers_tree.xview)
        self.convers_tree.config(yscrollcommand=self.tree_scrollbar_y.set, xscrollcommand=self.tree_scrollbar_x.set)

        self.convers_tree.pack(side="left", fill="both", expand=True)
        self.tree_scrollbar_y.pack(side="right", fill="y")
        self.tree_scrollbar_x.pack(side="bottom", fill="x")

        # Search Bar
        self.search_frame = Frame(self.list_frame)
        Label(self.search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = Entry(self.search_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_conversations)
        self.search_frame.pack(side="top", fill="x", pady=(0, 5))
        ToolTip(self.search_entry,
                text="Search by Tags",
                bootstyle=("inverse-secondary"),
                wraplength=140)

    def _layout_widgets(self):
        self.input_frame.pack(side="top", fill="x", expand=False)
        self.list_frame.pack(side="bottom", fill="both", expand=True)

        self.input_frame.grid_columnconfigure(1, weight=1) # Allow the input fields to expand
        self.rowconfigure(1, weight=1) # Allow the convers list to expand vertically
        self.columnconfigure(0, weight=1) # Allow the convers list to expand horizontally


    def add_convers(self):
        ''' working with the current live conversation.
            The 'Conversations' box must be clear.
            The Description box and tags must have content.
            If so,
                then create a date-time.
                create a filename for the conversation: "cnv_yyyy-mm-dd_HH:MM:SS.json"
                copy the live conversation.json to convhist/files/cnv_yyyy-mm-dd_HH:MM:SS.json
                insert the "cnv_yyyy-mm-dd_HH:MM:SS.json" file name into the Conversation Name Entry field
                finish updating the default.json file process '''
        if not os.path.exists("conversation.json"):
            messagebox.showwarning("Input Error", "No current conversation present")
            return
        text = self.text_entry.get("1.0", END).strip()
        tags = [tag.strip() for tag in self.tags_entry.get().split(',') if tag.strip()]
        if text and tags:
            timenow = strftime('%Y-%m-%d_%H-%M-%S', localtime())
            cnv_filename = "cnv_" + timenow + ".json"
            cnv_path = str(Path("convhist", "files", cnv_filename))
            print(cnv_path)
            shutil.copy2("conversation.json", cnv_path)
            name = cnv_filename
            self.conversations.append({"name": name, "text": text, "tags": tags})
            self.clear_fields()
            self.refresh_convers_list()
            self.save_conversations()
        else:
            messagebox.showwarning("Input Missing", "First type a description and provide tags.")

    def update_convers(self):
        ''' change Description and Tags fields only '''
        selected_item = self.convers_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a convers to update.")
            return

        messagebox.showwarning("Warning", "DO NOT CHANGE CONVERSATION FILE NAME")
        index = self.convers_tree.index(selected_item)
        name = self.name_entry.get().strip()
        text = self.text_entry.get("1.0", END).strip()
        tags = [tag.strip() for tag in self.tags_entry.get().split(',') if tag.strip()]

        if name and text:
            self.conversations[index] = {"name": name, "text": text, "tags": tags}
            self.clear_fields()
            self.refresh_convers_list()
            self.save_conversations()
        else:
            messagebox.showwarning("Input Error", "convers Name and Text cannot be empty.")

    def delete_convers(self):
        ''' Remove the saved conversation file '''
        selected_item = self.convers_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a convers to delete.")
            return

        file_path = str(Path("convhist", "files", self.name_entry.get().strip()))

        if not os.path.exists(file_path):
            messagebox.showerror("File Error", file_path + " is not found in files directory.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this convers?"):
            index = self.convers_tree.index(selected_item)
            del self.conversations[index]
            self.clear_fields()
            self.refresh_convers_list()
            self.save_conversations()
            os.remove(file_path)

    def copy_conversation(self):
        ''' Copy the selected (saved) conversation back as conversation.json '''
        selected_item = self.convers_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a saved conversation.")
            return
        cnv_filename = self.name_entry.get().strip()
        cnv_path = Path("convhist", "files", cnv_filename)
        shutil.copy2(cnv_path, "conversation.json")
        with open("restored", "w", encoding="utf-8") as fout:
            fout.write("marker\n")
        messagebox.showinfo("Copied", cnv_filename + " now Restored to Live")


    def select_conversation(self, event=None):
        selected_item = self.convers_tree.focus()
        if selected_item:
            index = self.convers_tree.index(selected_item)
            convers = self.conversations[index]
            self.name_entry.delete(0, END)
            self.name_entry.insert(0, convers["name"])
            self.text_entry.delete("1.0", END)
            self.text_entry.insert("1.0", convers["text"])
            self.tags_entry.delete(0, END)
            self.tags_entry.insert(0, ", ".join(convers["tags"]))
        else:
            self.clear_fields()

    def refresh_convers_list(self, filtered_conversations=None):
        for i in self.convers_tree.get_children():
            self.convers_tree.delete(i)

        conversations_to_display = filtered_conversations if filtered_conversations is not None else self.conversations
        for convers in conversations_to_display:
            self.convers_tree.insert("", "end", values=(convers["name"], ", ".join(convers["tags"])))

    def filter_conversations(self, event=None):
        search_term = self.search_entry.get().lower()
        if not search_term:
            self.refresh_convers_list()
            return

        filtered_list = []
        for convers in self.conversations:
            if search_term in convers["name"].lower() or \
               search_term in convers["text"].lower() or \
               any(search_term in tag.lower() for tag in convers["tags"]):
                filtered_list.append(convers)
        self.refresh_convers_list(filtered_list)

    def load_conversations(self, filepath=None):
        if filepath:
            self.current_file = filepath
        elif self.current_file:
            filepath = self.current_file
        else: # Default to a directory/file in the script's directory if no other file is open
            # script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = histfile
            self.current_file = filepath

        if not os.path.exists(filepath):
            self.conversations = []
            self.refresh_convers_list()
            self.title(f"Conversations Manager - {os.path.basename(self.current_file)} (New File)")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.conversations = json.load(f)
            self.refresh_convers_list()
            self.title(f"Conversations Manager - {os.path.basename(self.current_file)}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Could not read conversations from {filepath}. Invalid JSON.")
            self.conversations = []
            self.refresh_convers_list()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading conversations: {e}")
            self.conversations = []
            self.refresh_convers_list()

    def save_conversations(self):
        if not self.current_file:
            self.save_conversations_as()
            return
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, indent=4)
            self.title(f"Conversations Manager - {os.path.basename(self.current_file)}")
            # messagebox.showinfo("Success", "conversations saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving conversations: {e}")

    def save_conversations_as(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir="convhist",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save conversations As"
        )
        if filepath:
            self.current_file = filepath
            self.save_conversations()

    def new_file(self):
        if self.conversations and messagebox.askyesno("Save Changes", "Do you want to save current conversations before creating a new one?"):
            self.save_conversations()
        self.conversations = []
        self.current_file = None
        self.clear_fields()
        self.refresh_convers_list()
        self.title("Conversations Manager - New File")

    def open_file(self):
        if self.conversations and messagebox.askyesno("Save Changes", "Do you want to save current conversations before opening a new file?"):
            self.save_conversations()

        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Open conversations File"
        )
        if filepath:
            self.load_conversations(filepath)

    def view_selected(self):
        cnv_path = Path("convhist","files",self.name_entry.get())
        subprocess.Popen([self.MyEditor, cnv_path])

    def clear_fields(self):
        self.name_entry.delete(0, END)
        self.text_entry.delete("1.0", END)
        self.tags_entry.delete(0, END)
        self.convers_tree.selection_remove(self.convers_tree.focus()) # Deselect item


    def save_location(self, e=None):
        ''' executes at WM_DELETE_WINDOW event - see below '''
        with open("promet", "w") as fout:
            fout.write(self.geometry())
        self.destroy()


if __name__ == "__main__":
    app = conversManagerApp()
    app.mainloop()
