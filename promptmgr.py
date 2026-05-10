# prompmgr.py
#
# TODO
#

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
import json
import os # Added for path handling
import configparser
from ttkbootstrap import *
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip

class PromptManagerApp(Tk):
    def __init__(self):
        super().__init__() # call Tk's constructor
        self.title("Prompt Manager")
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
        style = Style()
        style = Style(theme=MyTheme)

        self.prompts = []
        self.current_file = None

        self._create_widgets()
        self._layout_widgets()
        self.load_prompts() # Load prompts on startup

        # Add menu bar
        self._create_menu()

        # Add event bindings for Treeview selection
        self.prompt_tree.bind("<<TreeviewSelect>>", self.select_prompt)


    def _create_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_prompts)
        file_menu.add_command(label="Save As...", command=self.save_prompts_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

    def _create_widgets(self):
        # Input Frame
        self.input_frame = Frame(self)
        Label(self.input_frame, text="Prompt Name:").grid(row=0, column=0, sticky="w", pady=2)
        self.name_entry = Entry(self.input_frame, width=50, font=('Arial', 12, 'bold'))
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=5)

        Label(self.input_frame, text="Prompt Text:").grid(row=1, column=0, sticky="nw", pady=2)
        self.text_entry = Text(self.input_frame, width=50, height=10)
        self.text_entry.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        efont = Font(family="Monospace", size=11)
        self.text_entry.config(wrap="word",
                                font=efont,
                                undo=True,
                                padx=5,
                                tabs=(efont.measure(' ' * 4),))
        Label(self.input_frame, text="Tags (comma-separated):").grid(row=2, column=0, sticky="w", pady=2)
        self.tags_entry = Entry(self.input_frame, width=50, font=('Arial', 12, 'bold'))
        self.tags_entry.grid(row=2, column=1, sticky="ew", pady=2, padx=5)

        # Buttons Frame
        self.button_frame = Frame(self.input_frame)
        self.add_button = Button(self.button_frame, text="Add Prompt", command=self.add_prompt)
        self.update_button = Button(self.button_frame, text="Update Prompt", command=self.update_prompt)
        self.delete_button = Button(self.button_frame, text="Delete Prompt", command=self.delete_prompt)
        self.clear_button = Button(self.button_frame, text="Clear Fields", command=self.clear_fields)
        self.copy_button = Button(self.button_frame, text="Copy Text", command=self.copy_prompt_text)

        self.add_button.pack(side="left", padx=5)
        self.update_button.pack(side="left", padx=5)
        self.delete_button.pack(side="left", padx=5)
        self.clear_button.pack(side="left", padx=5)
        self.copy_button.pack(side="left", padx=5)

        self.button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        # Prompt List Frame
        self.list_frame = Frame(self)
        self.prompt_tree = ttk.Treeview(self.list_frame, columns=("Name", "Tags"), show="headings")
        self.prompt_tree.heading("Name", text="Prompt Name")
        self.prompt_tree.heading("Tags", text="Tags")
        self.prompt_tree.column("Name", width=200)
        self.prompt_tree.column("Tags", width=150)

        self.tree_scrollbar_y = Scrollbar(self.list_frame, orient="vertical", command=self.prompt_tree.yview)
        self.tree_scrollbar_x = Scrollbar(self.list_frame, orient="horizontal", command=self.prompt_tree.xview)
        self.prompt_tree.config(yscrollcommand=self.tree_scrollbar_y.set, xscrollcommand=self.tree_scrollbar_x.set)

        self.prompt_tree.pack(side="left", fill="both", expand=True)
        self.tree_scrollbar_y.pack(side="right", fill="y")
        self.tree_scrollbar_x.pack(side="bottom", fill="x")

        # Search Bar
        self.search_frame = Frame(self.list_frame)
        Label(self.search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = Entry(self.search_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_prompts)
        self.search_frame.pack(side="top", fill="x", pady=(0, 5))


    def _layout_widgets(self):
        self.input_frame.pack(side="top", fill="x", expand=False)
        self.list_frame.pack(side="bottom", fill="both", expand=True)

        self.input_frame.grid_columnconfigure(1, weight=1) # Allow the input fields to expand
        self.rowconfigure(1, weight=1) # Allow the prompt list to expand vertically
        self.columnconfigure(0, weight=1) # Allow the prompt list to expand horizontally


    def add_prompt(self):
        name = self.name_entry.get().strip()
        text = self.text_entry.get("1.0", END).strip()
        tags = [tag.strip() for tag in self.tags_entry.get().split(',') if tag.strip()]

        if name and text:
            self.prompts.append({"name": name, "text": text, "tags": tags})
            self.clear_fields()
            self.refresh_prompt_list()
            self.save_prompts()
        else:
            messagebox.showwarning("Input Error", "Prompt Name and Text cannot be empty.")

    def update_prompt(self):
        selected_item = self.prompt_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a prompt to update.")
            return

        index = self.prompt_tree.index(selected_item)
        name = self.name_entry.get().strip()
        text = self.text_entry.get("1.0", END).strip()
        tags = [tag.strip() for tag in self.tags_entry.get().split(',') if tag.strip()]

        if name and text:
            self.prompts[index] = {"name": name, "text": text, "tags": tags}
            self.clear_fields()
            self.refresh_prompt_list()
            self.save_prompts()
        else:
            messagebox.showwarning("Input Error", "Prompt Name and Text cannot be empty.")

    def delete_prompt(self):
        selected_item = self.prompt_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a prompt to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this prompt?"):
            index = self.prompt_tree.index(selected_item)
            del self.prompts[index]
            self.clear_fields()
            self.refresh_prompt_list()
            self.save_prompts()

    def select_prompt(self, event=None):
        selected_item = self.prompt_tree.focus()
        if selected_item:
            index = self.prompt_tree.index(selected_item)
            prompt = self.prompts[index]
            self.name_entry.delete(0, END)
            self.name_entry.insert(0, prompt["name"])
            self.text_entry.delete("1.0", END)
            self.text_entry.insert("1.0", prompt["text"])
            self.tags_entry.delete(0, END)
            self.tags_entry.insert(0, ", ".join(prompt["tags"]))
        else:
            self.clear_fields()

    def refresh_prompt_list(self, filtered_prompts=None):
        for i in self.prompt_tree.get_children():
            self.prompt_tree.delete(i)

        prompts_to_display = filtered_prompts if filtered_prompts is not None else self.prompts
        for prompt in prompts_to_display:
            self.prompt_tree.insert("", "end", values=(prompt["name"], ", ".join(prompt["tags"])))

    def filter_prompts(self, event=None):
        search_term = self.search_entry.get().lower()
        if not search_term:
            self.refresh_prompt_list()
            return

        filtered_list = []
        for prompt in self.prompts:
            if search_term in prompt["name"].lower() or \
               search_term in prompt["text"].lower() or \
               any(search_term in tag.lower() for tag in prompt["tags"]):
                filtered_list.append(prompt)
        self.refresh_prompt_list(filtered_list)

    def load_prompts(self, filepath=None):
        if filepath:
            self.current_file = filepath
        elif self.current_file:
            filepath = self.current_file
        else: # Default to a file in the script's directory if no other file is open
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, "prompts/prompts.json")
            self.current_file = filepath

        if not os.path.exists(filepath):
            self.prompts = []
            self.refresh_prompt_list()
            self.title(f"Prompt Manager - {os.path.basename(self.current_file)} (New File)")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.prompts = json.load(f)
            self.refresh_prompt_list()
            self.title(f"Prompt Manager - {os.path.basename(self.current_file)}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Could not read prompts from {filepath}. Invalid JSON.")
            self.prompts = []
            self.refresh_prompt_list()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading prompts: {e}")
            self.prompts = []
            self.refresh_prompt_list()

    def save_prompts(self):
        if not self.current_file:
            self.save_prompts_as()
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=4)
            self.title(f"Prompt Manager - {os.path.basename(self.current_file)}")
            # messagebox.showinfo("Success", "Prompts saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving prompts: {e}")

    def save_prompts_as(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir="prompts",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Prompts As"
        )
        if filepath:
            self.current_file = filepath
            self.save_prompts()

    def new_file(self):
        if self.prompts and messagebox.askyesno("Save Changes", "Do you want to save current prompts before creating a new one?"):
            self.save_prompts()
        self.prompts = []
        self.current_file = None
        self.clear_fields()
        self.refresh_prompt_list()
        self.title("Prompt Manager - New File")

    def open_file(self):
        if self.prompts and messagebox.askyesno("Save Changes", "Do you want to save current prompts before opening a new file?"):
            self.save_prompts()

        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Open Prompts File"
        )
        if filepath:
            self.load_prompts(filepath)


    def clear_fields(self):
        self.name_entry.delete(0, END)
        self.text_entry.delete("1.0", END)
        self.tags_entry.delete(0, END)
        self.prompt_tree.selection_remove(self.prompt_tree.focus()) # Deselect item

    def copy_prompt_text(self):
        selected_item = self.prompt_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a prompt to copy its text.")
            return

        index = self.prompt_tree.index(selected_item)
        prompt_text = self.prompts[index]["text"]
        self.clipboard_clear()
        self.clipboard_append(prompt_text)
        # messagebox.showinfo("Copied", "Prompt text copied to clipboard!")
        self.show_auto_close("Copied", "Prompt text copied to clipboard!", 2000)

    def show_auto_close(self, title="Info",
                        message="This will close in 2 seconds",
                        delay=2000):
        ''' Method to display a momentary message to the user '''
        top = Toplevel(self)
        top.title(title)
        top.overrideredirect(True)
        top.transient(self)
        top.resizable(False, False)

        Label(top, text=message).pack()
        # Optional: a manual close button
        Button(top, text="OK", command=top.destroy).pack(pady=(0, 10))
        # Center near the parent (simple positioning)
        top.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (top.winfo_width() // 2)
        y = self.winfo_rooty() # + (self.winfo_height() // 2)  - (top.winfo_height() // 2)
        top.geometry("+%d+%d" % (x, y))

        top.after(delay, top.destroy)  # auto-close after delay milliseconds
        top.protocol("WM_DELETE_WINDOW", top.destroy)
        top.grab_set()
        top.focus_set()
        top.wait_window()

    def save_location(self, e=None):
        ''' executes at WM_DELETE_WINDOW event - see below '''
        with open("promet", "w") as fout:
            fout.write(self.geometry())
        self.destroy()


if __name__ == "__main__":
    app = PromptManagerApp()
    app.mainloop()

