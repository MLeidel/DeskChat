#!/usr/bin/python3

'''
descai.py
Linux and Windows ONLY
Apr 2026 - added local models
    by Michael Leidel

Disclaimer: This software is provided free of charge and "as is," without any warranties,
express or implied. The author and contributors assume no responsibility for any damages,
data loss, or other issues arising from its use. Use at your own risk.

'''
import os
import sys
import time
import configparser
import urllib.parse
import subprocess
import webbrowser
import platform
import json
import markdown
import re
from time import localtime, strftime
from tkinter import TclError
from tkinter import Listbox
from pathlib import Path
from tkinter.font import Font
from tkinter import messagebox
from tkinter import simpledialog
from ttkbootstrap import *
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
from openai import OpenAI
from google.genai import types
from ollama import Client
from ollama import chat
from groq import Groq
import anthropic
import vocvlc

#import google.generativeai as genai
from google import genai
from google.genai import types


apptitle = "DescAI 1.5 "

class Application(Frame):
    ''' This tkinter GUI app provides a flexible dual vertical pane
        main window with command buttons at the bottom. Other commands
        are available via hot keys. AI prompts go in the top pane
        and the AI responses go in the bottom pane.

        Currently the API code supports many
        Gpt, Claude, Gemini, Ollama, and Groq LLM's.
    '''
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.pack(fill=BOTH, expand=True, padx=4, pady=4)
        self.Saved = True
        self.cpath = "conversation.json"
        self.playback = False

        # get settings from ini file
        config = configparser.ConfigParser()
        config.read('options.ini')
        self.MyTheme    = config['Main']['theme']
        self.MyPath     = config['Main']['path']
        self.MyFntQryF  = config['Main']['fontqryfam']
        self.MyFntQryZ  = config['Main']['fontqrysiz']
        self.MyFntGptF  = config['Main']['fontgptfam']
        self.MyFntGptZ  = config['Main']['fontgptsiz']
        self.MyModel    = config['Main']['engine']
        self.MyButtons  = config['Main']['btncolor'] + "-outline"
        self.MyEditor   = config['Main']['editor']
        self.MyFile     = config['Main']['tempfile']
        self.MyVoice    = config['Main']['voice']
        self.MyColor    = config['Main']['color']
        self.MySystem   = config['Main']['system']
        self.MyTemper   = float(config['Main']['temper'])
        self.MyMd1      = config['Main']['md1']
        self.MyMd2      = config['Main']['md2']
        self.MyMd3      = config['Main']['md3']
        self.TOPFRAME   = int(config['Main']['top_frame'])

        with open("models.dat", 'r', encoding='utf-8') as f:
            self.MyModels = [line.strip() for line in f if line.strip()]

        self.MyKey = "GPTKEY"  # Claude is hardcoded to CLDKEY
        self.MyTitle = apptitle + self.MyModel

        self.set_intro()
        self.create_widgets()

    def create_widgets(self):
        ''' creates GUI for app '''

        # expand widget to fill the grid
        self.columnconfigure(1, weight=1, pad=5)
        self.columnconfigure(2, weight=1, pad=5)
        self.rowconfigure(1, weight=1, pad=5)
        self.rowconfigure(2, weight=1, pad=5)

        # Create a vertical PanedWindow to hold both text widgets
        self.paned = PanedWindow(self, orient=VERTICAL)
        self.paned.grid(row=1, rowspan=2, column=1, columnspan=2, sticky='nsew')

        # --- Query frame (top pane) ---
        self.query_frame = Frame(self.paned)
        self.query = Text(self.query_frame)
        self.query.pack(side=LEFT, fill=BOTH, expand=True)
        efont = Font(family=self.MyFntQryF, size=self.MyFntQryZ)
        self.query.configure(font=efont)
        self.query.config(wrap="word",
                          undo=True,
                          width=50,
                          height=self.TOPFRAME,
                          padx=5,
                          tabs=(efont.measure(' ' * 4),))
        self.scrolly_query = Scrollbar(self.query_frame, orient=VERTICAL,
                                        command=self.query.yview)
        self.scrolly_query.pack(side=RIGHT, fill=Y)
        self.query['yscrollcommand'] = self.scrolly_query.set
        self.paned.add(self.query_frame)

        # --- Response frame (bottom pane) ---
        self.txt_frame = Frame(self.paned)
        self.txt = Text(self.txt_frame, fg=self.MyColor)
        self.txt.pack(side=LEFT, fill=BOTH, expand=True)
        efont = Font(family=self.MyFntGptF, size=self.MyFntGptZ)
        self.txt.configure(font=efont)
        self.txt.config(wrap="word",
                        undo=True,
                        width=50,
                        height=12,
                        padx=5,
                        tabs=(efont.measure(' ' * 4),))
        self.scrolly_txt = Scrollbar(self.txt_frame, orient=VERTICAL,
                                      command=self.txt.yview)
        self.scrolly_txt.pack(side=RIGHT, fill=Y)
        self.txt['yscrollcommand'] = self.scrolly_txt.set
        self.paned.add(self.txt_frame)


        # BUTTON FRAME
        btn_frame = Frame(self)
        btn_frame.grid(row=4, column=1, sticky='w')

        self.new = Button(btn_frame, text='New',
                            command=self.on_new,
                            bootstyle=self.MyButtons)
        self.new.grid(row=1, column=2, sticky='w',
                   pady=(5, 0), padx=(5, 7))

        self.view = Button(btn_frame, text='View',
                            command=self.on_view_file,
                            bootstyle=self.MyButtons)
        self.view.grid(row=1, column=4, sticky='w',
                   pady=(5, 0))

        self.open = Button(btn_frame, text='Text',
                            command=self.on_md_open,
                            bootstyle=self.MyButtons)
        self.open.grid(row=1, column=6, sticky='w',
                     pady=(5, 0), padx=5)

        self.md = Button(btn_frame, text='Html',
                            command=self.on_md_render,
                            bootstyle=self.MyButtons)
        self.md.grid(row=1, column=7, sticky='w',
                     pady=(5, 0), padx=(0, 5))

        self.opts = Button(btn_frame, text='Options',
                            command=self.options,
                            bootstyle=self.MyButtons)
        self.opts.grid(row=1, column=8, sticky='w',
                   pady=(5, 0), padx=5)

        self.sub = Button(btn_frame,
                            text='Submit Query',
                            command=self.on_submit, width=15,
                            bootstyle=self.MyButtons)
        self.sub.grid(row=1, column=9, sticky='w',
                   pady=(5, 0), padx=(5,5))

        self.vw = IntVar()  # Tooggle Web Search Checkbutton
        self.web = Checkbutton(btn_frame, variable=self.vw,
                    text='Web', bootstyle=(self.MyButtons + "-toolbutton"))
        self.web.grid(row=1, column=10, sticky='w', pady=(5, 0), padx=(5, 5))

        self.vcmbo_model = StringVar()
        self.cmbo_model = Combobox(btn_frame, textvariable=self.vcmbo_model, width=18, state="readonly")
        self.cmbo_model['values'] = self.MyModels
        self.cmbo_model.grid(row=1, column=11, sticky='w', pady=(5, 0), padx=(5, 5))
        self.cmbo_model.bind('<<ComboboxSelected>>', self.onComboSelect)

       # END BUTTON FRAME

        cls = Button(self, text='Close',
                    command=self.exit_program,
                    bootstyle=self.MyButtons)
        cls.grid(row=4, column=2, columnspan=2, sticky='e',
                 pady=(5,0), padx=5)

        # Popup menus - for self.query Text widgets
        self.popup_query = Menu(root, tearoff=0)
        self.popup_query.add_command(label="Copy",
                               command=lambda: self.popquery(1))
        self.popup_query.add_command(label="Paste",
                               command=lambda: self.popquery(2))
        self.popup_query.add_separator()
        self.popup_query.add_command(label="Copy All",
                                     command=lambda: self.popquery(3))
        self.popup_query.add_separator()
        self.popup_query.add_command(label="Larger",
                                     command=lambda: self.popquery(4))
        self.popup_query.add_command(label="Smaller",
                                     command=lambda: self.popquery(5))
        self.popup_query.add_separator()
        self.popup_query.add_command(label="Browser",
                                     command=lambda: self.popquery(6))

        # Popup menus - for self.txt Text widgets
        self.popup_txt = Menu(tearoff=0)
        self.popup_txt.add_command(label="Copy",
                               command=lambda: self.poptxt(1))
        self.popup_txt.add_command(label="Paste",
                               command=lambda: self.poptxt(2))
        self.popup_txt.add_separator()
        self.popup_txt.add_command(label="Copy All",
                                     command=lambda: self.poptxt(3))


        # Bindings

        root.bind("<Control-r>", lambda event: self.query.delete('1.0', 'end'))
        root.bind("<Alt-p>", self.create_window)
        root.bind("<Control-h>", self.on_kb_help)  # show hotkey help
        root.bind("<Control-q>", self.exit_program)  # Close button
        root.bind("<Control-g>", self.on_submit)  # Submit Query button
        root.bind("<Control-Return>", self.on_submit)  # Submit Query button
        root.bind("<Control-Shift-S>", self.speak_text)  # speak query response
        root.bind("<Control-Shift-D>", self.delete_log)
        root.bind("<Control-f>", self.find_text)
        root.bind("<Control-n>", self.find_next)
        root.bind("<Control-e>", self.on_md_open)
        root.bind("<Control-j>", self.open_selected_url)  # open selected URL in browser
        self.query.bind("<Button-3>", self.do_pop_query)
        self.txt.bind("<Button-3>", self.do_pop_txt)
        # Bind events for real-time highlighting
        self.txt.bind("<KeyRelease>", self.on_key_release)
        self.txt.bind("<Button-1>", self.on_click)

        # Configure tags for different Markdown elements
        self.txt.tag_configure("headings",  foreground=self.MyMd1)
        self.txt.tag_configure("hrule",     foreground=self.MyMd1)
        self.txt.tag_configure("bold",      foreground=self.MyMd2)
        self.txt.tag_configure("italic",    foreground=self.MyMd2)
        self.txt.tag_configure("code",      foreground=self.MyMd3, font=("Noto Sans Mono", 10))

        self.txt.config(fg=self.MyColor)  # refresh txt foreground

        # ToolTips
        ToolTip(self.new,
                text="Start new conversation",
                bootstyle=(INVERSE),
                wraplength=140)
        ToolTip(self.view,
                text="View current log",
                bootstyle=(INVERSE),
                wraplength=140)
        ToolTip(self.sub,
                text="Ctrl-Enter to Append",
                bootstyle=(INVERSE),
                wraplength=140)
        ToolTip(self.md,
                text="markdown to browser",
                bootstyle=(INVERSE),
                wraplength=140)
        ToolTip(self.open,
                text="markdown to text editor",
                bootstyle=(INVERSE),
                wraplength=140)
        ToolTip(self.web,
                text="Toggle Web Search. N/A for claude.",
                bootstyle=(INVERSE),
                wraplength=140)

        self.txt.delete("1.0", END)
        self.txt.insert("1.0", self.set_intro())

        # Variable to store the current search term and the index of the last found match.
        self.search_term = None
        self.last_found_index = "1.0"

        # Create a tag to highlight the search result.
        self.txt.tag_config("highlight", background="light grey", foreground="black")

        self.query.focus_set()

        #
        # on startup check for conversation.json file
        # The user may have the option to continue the converstation or start fresh.
        #
        self.conversation = self.load_buffer(self.cpath)

        if self.conversation == []:
            if not self.MyModel.startswith("claude"):
                # and not self.MyModel.startswith("gemini":
                self.conversation = [
                    {"role": "system", "content": self.MySystem}
                ]
            if os.path.isfile(self.cpath):
                os.remove(self.cpath)
        else:
            self.on_new()

#----------------------------------------------------------------------

    def set_intro(self):
        ''' A "start" screen providing helpful information
            about the app and its settings.
        '''
        intro = f'''
        Welcome to {apptitle}
            a GUI desktop AI client to converse with
            Gpt, Claude, Gemini, Groq,
            Ollama, and Deepseek LLMs

        Model: {self.MyModel}
        role: {self.MySystem}
        qheight: {self.TOPFRAME}
        editor: {self.MyEditor}
        voice: {self.MyVoice}
        color: {self.MyColor}
        font1: {self.MyFntQryF}
        f1 size: {self.MyFntQryZ}
        font2: {self.MyFntGptF}
        f2 size: {self.MyFntGptZ}

        Use Ctrl-H for list of keyboard commands

        Registered API keys are required to be set
        as system environment variables.
        See https://github.com/MLeidel/DescAI for details.

        https://auth.openai.com/log-in
        https://platform.claude.com/dashboard
        https://aistudio.google.com/api-keys
        https://ollama.com/
        https://console.groq.com/keys
        https://platform.deepseek.com
        '''

        return intro


    def display_intro(self):
        self.txt.delete("1.0", END)
        self.txt.insert("1.0", self.set_intro())


    def show_prompts(self, fword: str):
        ''' Open and display the prompt text file. '''
        self.query.delete("1.0", END)
        prmt = f"prompts/{fword}.md"
        try:
            self.query.insert("1.0", open(prmt).read())
        except Exception as e:
            messagebox.showerror("Prompt File", f"{prmt} not found.")


    '''         API FUNCTIONS START HERE
        ▄▖▄▖▄▖
        ▌ ▙▌▐
        ▙▌▌ ▐
    '''
    def api_gpt(self): # OpenAI models ...
        '''  '''
        if self.vw.get() == 1:  #  requesting web search tool
            # print("web search")
            try:
                client = OpenAI(api_key=os.environ.get("GPTKEY"))
                response = client.responses.create(
                    model=self.MyModel,
                    tools=[{"type": "web_search"}],
                    input=self.conversation
                )
                ai_text = response.output_text
            except Exception as e:
                messagebox.showerror("Client Error", str(e))
                ai_text = ""
        else:
            # regular OpenAI request
            try:
                client = OpenAI(api_key=os.environ.get("GPTKEY"))
                resp  = client.chat.completions.create(
                model = self.MyModel,
                messages = self.conversation)
                content = resp.choices[0].message.content.strip()
                ai_text = content
            except Exception as e:
                messagebox.showerror("Client Error", str(e))
                ai_text = ""

        return ai_text

    '''
        ▄▖▜      ▌    ▖▖  ▘▌
        ▌ ▐ ▀▌▌▌▛▌█▌  ▙▌▀▌▌▙▘▌▌
        ▙▖▐▖█▌▙▌▙▌▙▖  ▌▌█▌▌▛▖▙▌
    '''
    def api_claude_haiku(self):
        '''  '''
        client = anthropic.Anthropic(
            api_key=os.environ.get("CLDKEY")
        )

        if self.vw.get() == 1:
            messagebox.showwarning("Web Search","Web Search is not available with claude-haidu model.")
            self.query.delete("1.0", END)
            self.display_intro()
            return ""


        system_prompt = [
            {
                "type": "text",
                "text": self.MySystem,
                "cache_control": {"type": "ephemeral"} # Breakpoint 1
            }
        ]

        try:
            # Create the message request
            response = client.messages.create(
                model=self.MyModel, # Official ID for Haiku 4.5
                max_tokens=2048,
                temperature=float(self.MyTemper),  # REMOVE for Sonnet model
                system=system_prompt,
                cache_control={"type": "ephemeral"},
                messages=self.conversation
            )

            # Extract response text ONLY for HAIKU model
            ai_text = response.content[0].text

        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text

    '''
        ▄▖▜      ▌    ▄▖        ▗
        ▌ ▐ ▀▌▌▌▛▌█▌  ▚ ▛▌▛▌▛▌█▌▜▘
        ▙▖▐▖█▌▙▌▙▌▙▖  ▄▌▙▌▌▌▌▌▙▖▐▖
    '''
    def api_claude_sonnet(self):
        '''  '''
        client = anthropic.Anthropic(
            api_key=os.environ.get("CLDKEY")
        )

        system_prompt = [
            {
                "type": "text",
                "text": self.MySystem,
                "cache_control": {"type": "ephemeral"} # Breakpoint 1
            }
        ]

        try:
            # Create the message request
            response = client.messages.create(
                model=self.MyModel,
                max_tokens=4096,
                **({"tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]} if self.vw.get() == 1 else {}),
                # 'thinking' allows Sonnet to solve harder logic/coding bugs
                thinking={
                    "type": "enabled",
                    "budget_tokens": 1024
                },
                cache_control={"type": "ephemeral"},
                system=system_prompt,
                messages=self.conversation
            )

            # Sonnet 4.6 returns content in blocks (Thinking + Text)
            ai_text = ""
            for block in response.content:
                if block.type == "text":
                    ai_text += block.text

        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text

    '''
        ▄▖▜      ▌    ▄▖
        ▌ ▐ ▀▌▌▌▛▌█▌  ▌▌▛▌▌▌▛▘
        ▙▖▐▖█▌▙▌▙▌▙▖  ▙▌▙▌▙▌▄▌
                        ▌
    '''
    def api_claude_opus(self):
        '''  '''
        client = anthropic.Anthropic(
            api_key=os.environ.get("CLDKEY")
        )

        system_prompt = [
            {
                "type": "text",
                "text": self.MySystem,
                "cache_control": {"type": "ephemeral"} # Breakpoint 1
            }
        ]

        try:
            response = client.messages.create(
                model=self.MyModel,
                max_tokens=8192,
                **({"tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]} if self.vw.get() == 1 else {}),
                # 'thinking' allows Sonnet to solve harder logic/coding bugs
                thinking={
                    "type": "adaptive",
                },
                output_config={
                    "effort": "medium"
                },
                cache_control={"type": "ephemeral"},
                system=system_prompt,
                messages=self.conversation
            )

            ai_text = ""
            for block in response.content:
                if block.type == "text":
                    ai_text += block.text

        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text

    '''
        ▄▖      ▜     ▄▖     ▘  ▘
        ▌ ▛▌▛▌▛▌▐ █▌  ▌ █▌▛▛▌▌▛▌▌
        ▙▌▙▌▙▌▙▌▐▖▙▖  ▙▌▙▖▌▌▌▌▌▌▌
              ▄▌
    '''
    def api_gemini(self):
        '''  '''
        if self.vw.get() == 1:
            messagebox.showwarning("Web Search","Web Search is not available with Gemini models here.")
            self.query.delete("1.0", END)
            self.display_intro()
            return ""

        try:
            client = OpenAI(
                api_key=os.environ.get("api_key"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )

            response = client.chat.completions.create(
                model=self.MyModel,
                messages=self.conversation)

            ai_text = response.choices[0].message.content.strip()
        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text

    '''
        ▄▖▜ ▜          ▄▖▜      ▌
        ▌▌▐ ▐ ▀▌▛▛▌▀▌  ▌ ▐ ▛▌▌▌▛▌
        ▙▌▐▖▐▖█▌▌▌▌█▌  ▙▖▐▖▙▌▙▌▙▌
    '''
    def api_ollama_cloud(self):
        '''  '''
        if self.vw.get() == 1:
            messagebox.showwarning("Web Search","Web Search is not available with these Ollama models.")
            self.query.delete("1.0", END)
            self.display_intro()
            return ""

        client = Client(
            host='https://ollama.com',
            headers={
                'Authorization': f"Bearer {os.environ.get('OLLAMA_API_KEY')}"
            }
        )

        try:

            response = client.chat(
                model=self.MyModel,
                messages=self.conversation,
                stream=True
            )

            full_response = ""
            for chunk in response:
                content = chunk['message']['content']
                full_response += content

            ai_text = full_response

        except Exception as e:
            wx.MessageBox(str(e), 'Info', wx.OK | wx.ICON_ERROR)
            ai_text = ""

        return ai_text

    '''
        ▄▖
        ▌ ▛▘▛▌▛▌
        ▙▌▌ ▙▌▙▌
               ▌
    '''
    def api_groq(self):
        ''' method to access GROQ API '''
        try:

            client = Groq(
                # This is the default and can be omitted
                api_key=os.environ.get("GROQ_KEY"),
                default_headers={
                    "Groq-Model-Version": "latest"
                }
            )

            chat_completion = client.chat.completions.create(
                messages=self.conversation,
                model=self.MyModel
            )

            ai_text = chat_completion.choices[0].message.content

        except Exception as e:
            wx.MessageBox(str(e), 'Info', wx.OK | wx.ICON_ERROR)
            ai_text = ""

        return ai_text

    '''
        ▄             ▌
        ▌▌█▌█▌▛▌▛▘█▌█▌▙▘
        ▙▘▙▖▙▖▙▌▄▌▙▖▙▖▛▖
              ▌
    '''
    def api_deepseek(self):
        '''  '''
        if self.vw.get() == 1:
            messagebox.showwarning("Web Search","Web Search is not available with Deepseek")
            self.query.delete("1.0", END)
            self.display_intro()
            return ""

        try:
            client = OpenAI(api_key=os.environ.get('DSEEK1'), base_url="https://api.deepseek.com")
            resp  = client.chat.completions.create(
                model = self.MyModel,
                temperature = self.MyTemper,
                messages = self.conversation
            )
            content = resp.choices[0].message.content.strip()
            ai_text = content
        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text

    '''
        ▄▖▜ ▜          ▖       ▜
        ▌▌▐ ▐ ▀▌▛▛▌▀▌  ▌ ▛▌▛▘▀▌▐
        ▙▌▐▖▐▖█▌▌▌▌█▌  ▙▖▙▌▙▖█▌▐▖

    '''
    def api_ollama_local(self):
        '''  '''
        if self.vw.get() == 1:
            messagebox.showwarning("Web Search","Web Search is not available with these Ollama local.")
            self.query.delete("1.0", END)
            self.display_intro()
            return ""

        try:
            # remove the "-local" text appended to the model name
            mymodel = self.MyModel[:-6]

            response = chat(model=mymodel, messages=self.conversation)

            ai_text = response.message.content

        except Exception as e:
            messagebox.showerror("Client Error", str(e))
            ai_text = ""

        return ai_text


    #################
    ### ON SUBMIT ###
    #################

    def on_submit(self, event=None):
        ''' Event handler for Submit button (Ctrl-G).
            Handles all the APIs '''

        query = self.query.get("1.0", END).strip()

        # show prompt.md document
        if query.startswith("prompt"):
            fword = query.split()
            self.show_prompts(fword[0])
            return

        # begin submiting request
        self.txt.delete("1.0", END)
        self.txt.insert("1.0", "Thinking ..." )
        self.txt.update_idletasks()

        # start timer
        start_time = time.perf_counter()

        # add the user message (prompt)
        self.conversation.append(
            {"role": "user", "content": query}
        )

        # call the set chat completion API

        if self.MyModel.endswith("-local"):
            ai_text = self.api_ollama_local()
        elif self.MyModel.startswith("gpt"):
            ai_text = self.api_gpt()
        elif self.MyModel.startswith("claude-haiku"):
            ai_text = self.api_claude_haiku()
        elif self.MyModel.startswith("claude-sonnet"):
            ai_text = self.api_claude_sonnet()
        elif self.MyModel.startswith("claude-opus"):
            ai_text = self.api_claude_opus()
        elif self.MyModel.startswith("gemini"):
            ai_text = self.api_gemini()
        elif self.MyModel.endswith("cloud"):
            ai_text = self.api_ollama_cloud()
        elif self.MyModel.startswith("groq"):
            ai_text = self.api_groq()
        elif self.MyModel.startswith("deepseek"):
            ai_text = self.api_deepseek()
        else:
            ai_text = ""

        if ai_text == "":
            self.query.delete("1.0", END)
            self.display_intro()
            return

        # 3) add the assistant reply to history
        self.conversation.append(
            {"role": "assistant", "content": ai_text}
        )

        # 4) show it
        self.txt.delete("1.0", END)
        self.txt.insert("1.0", ai_text)
        # self.txt.tag_add('all_text', '1.0', 'end-1c')  ///
        self.after(400, self.highlight)
        # SAVE conversation to disk
        self.save_buffer(self.conversation, self.cpath)

        ### append to log ###

        # calculate time spent
        end_time = time.perf_counter()
        elapsed_seconds = end_time - start_time
        total_seconds = int(round(elapsed_seconds))
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        today = strftime("%a %d %b %Y", localtime())
        tm    = strftime("%H:%M", localtime())
        atk   = self.get_aprox_tokens(ai_text)
        with open(self.MyPath, "a", encoding="utf-8") as fout:
            fout.write("\n\n=== (%s) Chat on %s %s ===\n\n" % (self.MyModel, today, tm))
            fout.write(query + "\n\n+++ assistant +++\n\n")
            fout.write(ai_text + "\n")
            fout.write(f"\n====== Aprox Tokens {atk} === Time {minutes}:{seconds} ======" + "\n\n")
        # select the input query box
        self.query.tag_add("sel", "1.0", "end-1c")
        self.query.focus_set()

#----------------------------------------------------------------------

    def get_aprox_tokens(self, text) -> int:
        ''' Calculates aproximate/average tokens from text '''
        words = text.split()
        avtok = len(words) / 1.35
        return int(avtok)


    def new_conversation(self):
        ''' start new conversation '''
        self.conversation.clear()
        self.google_new = True  # Gemini API is temporary always
        # check for system message change
        usertext = self.query.get("1.0", END)
        if usertext.lower().startswith("instruct"):
            self.MySystem = usertext[9:].strip()
        # set the system message
        if self.MyModel.startswith("claude"):
            self.conversation = []
        else:
            self.conversation = [
                {"role": "system", "content": self.MySystem}
            ]
        if os.path.isfile(self.cpath):
            os.remove(self.cpath)
            messagebox.showinfo("Note", "The text of the previous conversation will remain in the log.")
        self.query.delete("1.0", END)
        self.display_intro()
        self.query.focus_set()

    def on_new(self):
        ''' Event handler for the New button.
        Optionally starts new conversation
        A new system prompt may be taken from the prompt
        area preceeded by the word `prompt` '''
        root.withdraw()
        result = messagebox.askyesno("Conversations",
                                        "Start a new conversation?")
        root.deiconify()
        if result is True:
            # start new conversation
            self.new_conversation()
        self.query.focus_set()

    def onComboSelect(self, e=None):
        ''' Selecting different AI model '''
        # warn of conversation reset
        if os.path.isfile(self.cpath):
            result = messagebox.askyesno("There is an exiting conversation",
                                            "Start a new conversation?")
            if result is False:
                self.vcmbo_model.set("")
                messagebox.showwarning("Change Model", "Cannot change model in an existing conversation.")
                return ""

        self.MyModel = self.vcmbo_model.get()
        self.MyTitle = apptitle + self.MyModel + " *"
        # update window caption and information
        root.title(self.MyTitle)
        self.new_conversation()  #  Note: cannot continue current conversation when switching models.

    def load_buffer(self, path):
        ''' Used only for OpenAI and only serves to verify the JSON '''
        try:
            with open(self.cpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # corrupted file -> start clean
            return []

    def save_buffer(self, buf, path):
        with open(self.cpath, "w", encoding="utf-8") as f:
            json.dump(buf, f, ensure_ascii=False, indent=2)


    def on_view_file(self):
        ''' View the user saved queries "log" file. '''
        if not os.path.isfile(self.MyPath):
            messagebox.showwarning(self.MyPath, "Empty - No File to view")
            return
        self.txt.delete("1.0", END)
        with open(self.MyPath, "r", encoding="utf-8") as fin:
            self.txt.insert("1.0", fin.read())
        self.txt.see(END)
        self.query.delete("1.0", END)
        self.after(400, self.highlight)



    def reLaunch(self):
        ''' close and re-open this instance '''
        wx.MessageBox('App will now close and re-open...')
        python = sys.executable
        #self.Destroy()
        self.on_close(None)
        os.execl(python, python, *sys.argv)


    def options(self, e=None):
        ''' Launch Options program and exit this program '''
        if platform.system() == "Windows":
            subprocess.call(["pythonw.exe", "options.py"])
        else:
            subprocess.call(["python3", "options.py"])
        # re-read configuration
        config = configparser.ConfigParser()
        config.read('options.ini')
        self.MyTheme = config['Main']['theme']
        self.MyPath  = config['Main']['path']
        self.MyFntQryF = config['Main']['fontqryfam']
        self.MyFntQryZ = config['Main']['fontqrysiz']
        self.MyFntGptF = config['Main']['fontgptfam']
        self.MyFntGptZ = config['Main']['fontgptsiz']
        self.MyModel   = config['Main']['engine']
        self.MyButtons = config['Main']['btncolor']
        self.MyEditor = config['Main']['editor']
        self.MyFile   = config['Main']['tempfile']
        self.MyVoice  = config['Main']['voice']
        self.MyColor  = config['Main']['color']
        self.MySystem = config['Main']['system']
        self.TOPFRAME = int(config['Main']['top_frame'])
        # if len(self.MyKey) < 16:
        #     self.MyKey = os.environ.get(self.MyKey)  # Using ENV var instead of actual key string.
        # re-set the items and change font/size
        efont = Font(family=self.MyFntQryF, size=self.MyFntQryZ)
        self.query.configure(font=efont, height=self.TOPFRAME)
        efont = Font(family=self.MyFntGptF, size=self.MyFntGptZ)
        self.txt.configure(font=efont)
        style = Style()
        style = Style(theme=self.MyTheme)
        self.MyTitle = apptitle + self.MyModel
        root.title(self.MyTitle)
        self.txt.delete("1.0", END)
        self.txt.insert("1.0", self.set_intro())
        self.txt.config(fg=self.MyColor)
        self.new_conversation()  # Note: cannot continue current conversation when switching models.


    def getmdtext(self):
        ''' get all or selected text '''
        if self.txt.tag_ranges("sel"):
            text = self.txt.selection_get()
        else:  # Select All
            self.txt.focus()
            self.txt.tag_add(SEL, '1.0', END)
            self.txt.mark_set(INSERT, '1.0')
            self.txt.see(INSERT)
            if self.txt.tag_ranges("sel"):
                text = self.txt.selection_get()
                self.txt.tag_remove(SEL, "1.0", END)
        return text


    def on_md_open(self, e=None):
        ''' open txt (MD) in your text editor '''
        text = self.getmdtext()
        filename = os.getcwd() + '/' + self.MyFile
        with open(filename, 'w') as f:
            f.write(text)
        # print(self.MyEditor, filename)
        subprocess.Popen([self.MyEditor, filename])
        # os.system(self.MyEditor + " " + filename)

    def on_md_render(self, e=None):
        ''' render txt (MD) to html and show window '''
        text = self.getmdtext()
        # convert MD to HTML
        H = markdown.markdown(text,
                              extensions=['tables','fenced_code'])
        # write to file
        html_path = Path(__file__).resolve().parent / f"{self.MyFile}.html"  # script's directory + file
        with open(html_path, 'w') as f:
            f.write(H)
        webbrowser.open_new_tab(html_path.as_uri())  # opens in default browser


    def speak_text(self, e=None):
        ''' Speak the query response text
            key, voc, ins, fou, inp
        '''
        self.MyTitle = apptitle + self.MyModel + " <<Voice Generation>>"
        root.title(self.MyTitle)
        self.txt.update_idletasks()
        text = self.getmdtext()  # get selected or all text
        filename = self.get_unique_filename()
        filename = "speech/" + filename
        x = vocvlc.textospeech(self.MyKey, self.MyVoice, 'normal', filename, text)
        if x != 0:
            messagebox.showerror("vocvlc Error", "There is a problem with the voice file")
        else:
            p = self.MyTitle.find(" <<V")
            self.MyTitle = self.MyTitle[:p]
            root.title(self.MyTitle)
            self.txt.update_idletasks()


    def get_unique_filename(self, directory: str = ".",
                            base_name: str = "speech", extension: str = "mp3") -> str:
        '''
        Generate a unique filename in the format: speech_N.ext

        Args:
            directory: Directory where files will be stored (default: current directory)
            base_name: Base name for the file (default: "speech")
            extension: File extension without dot (default: "mp3")

        Returns:
            A unique filename string
        '''
        counter = 1
        while True:
            filename = f"{base_name}_{counter}.{extension}"
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                return filename
            counter += 1


    def on_kb_help(self, e=None):
        ''' display hot keys message '''
        msg = '''
Ctrl-Shift-D > Delete Log
Ctrl-Shift-S > Speak the Text
Ctrl-Return > Submit Query
Ctrl-G > Submit Query
Ctrl-H > HotKeys help
Ctrl-F > Find Text
Ctrl-N > Find Next Text
Ctrl-J > Open Selected URL
Ctrl-Q > Exit Program no ask
Ctrl-R > Clear prompt area
Ctrl-E > Open in Text Editor
Alt-P > Open Prompt Manager
        '''
        messagebox.showinfo("Hot Keys Help", msg)


    def do_pop_query(self, event):
        ''' handles right-click for context menu '''
        popup = tk.Toplevel(root)
        popup.wm_overrideredirect(True)  # no window decorations
        popup.attributes("-topmost", True)
        popup.geometry("+%d+%d" % (event.x_root, event.y_root))

        frame = tk.Frame(popup, bd=0)
        frame.pack()

        items = [
            ("Copy", lambda: (popup.destroy(), self.popquery(1))),
            ("Paste", lambda: (popup.destroy(), self.popquery(2))),
            ("Copy All", lambda: (popup.destroy(), self.popquery(3))),
            ("Prompt Mgr", lambda: (popup.destroy(), self.popquery(4))),
            ("Clear", lambda: (popup.destroy(), self.popquery(5))),
            ("Close", lambda: (popup.destroy())),
        ]


        for text, cmd in items:
            b = tk.Button(frame, text=text, anchor="w", command=lambda c=cmd: (popup.destroy(), c()))
            b.pack(fill="x", padx=8, pady=4)  # padding around each item


    def do_pop_txt(self, event):
        ''' handles right-click for txt menu '''
        popup = tk.Toplevel(root)
        popup.wm_overrideredirect(True)  # no window decorations
        popup.attributes("-topmost", True)
        popup.geometry("+%d+%d" % (event.x_root, event.y_root))

        frame = tk.Frame(popup, bd=0)
        frame.pack()

        items = [
            ("Copy", lambda: (popup.destroy(), self.poptxt(1))),
            ("Paste", lambda: (popup.destroy(), self.poptxt(2))),
            ("Copy All", lambda: (popup.destroy(), self.poptxt(3))),
            ("Google Text", lambda: (popup.destroy(), self.poptxt(4))),
            ("Find Text", lambda: (popup.destroy(), self.poptxt(5))),
            ("KB Help", lambda: (popup.destroy(), self.poptxt(6))),
            ("Open URL", lambda: (popup.destroy(), self.poptxt(7))),
            ("Close", lambda: (popup.destroy())),
        ]

        for text, cmd in items:
            b = tk.Button(frame, text=text, anchor="w", command=lambda c=cmd: (popup.destroy(), c()))
            b.pack(fill="x", padx=8, pady=4)  # padding around each item

    def popquery(self, n):
        ''' Routes query context menu actions '''
        if n == 1:  # Copy to clipboard
            root.clipboard_clear()  # clear clipboard contents
            if self.query.tag_ranges("sel"):
                root.clipboard_append(self.query.selection_get())  # append new value to clipbaord
        elif n == 2:  # Paste from clipboard
            root.update()
            inx = self.query.index(INSERT)
            try:
                self.query.insert(inx, root.clipboard_get())
            except Exception as e:
                return
        elif n == 3:  # Copy All
            self.query.focus()
            self.query.tag_add(SEL, '1.0', END)
            self.query.mark_set(INSERT, '1.0')
            self.query.see(INSERT)
            root.clipboard_clear()  # clear clipboard contents
            if self.query.tag_ranges("sel"):  # append new value to clipbaord
                root.clipboard_append(self.query.selection_get())
                self.query.tag_remove(SEL, "1.0", END)
        elif n == 4:  # Prompt Manager
            self.create_window(None)
        elif n == 5:  # clear prompt text area
            self.query.delete('1.0', 'end')

    def poptxt(self, n):
        ''' Routes txt context menu actions '''
        if n == 1:  # Copy
            root.clipboard_clear()  # clear clipboard contents
            root.clipboard_append(self.txt.selection_get())  # append new value to clipbaord
        elif n == 2:  # Paste
            inx = self.txt.index(INSERT)
            self.txt.insert(inx, root.clipboard_get())
        elif n == 3:  # Select All
            self.txt.focus()
            self.txt.tag_add(SEL, '1.0', END)
            self.txt.mark_set(INSERT, '1.0')
            self.txt.see(INSERT)
            root.clipboard_clear()  # clear clipboard contents
            if self.txt.tag_ranges("sel"):  # append new value to clipbaord
                root.clipboard_append(self.txt.selection_get())
                self.txt.tag_remove(SEL, "1.0", END)
        elif n == 4:   # search for selected text using browser
            search = self.txt.selection_get()
            if len(search) > 2:
                webbrowser.open("https://www.google.com/search?q=" + search)
        elif n == 5:  # find text in the response window
            self.find_text()
        elif n == 6:  # keyboard help
            self.on_kb_help()
        elif n == 7:  # open browser with selected URL
            self.open_selected_url()


    def find_text(self, event=None):
        ''' Ask the user for the text to search
            then find and highlight the text if found.'''
        term = simpledialog.askstring("Find", "Enter text to search:")
        if term:
            self.search_term = term
            # Remove any previous highlights.
            self.txt.tag_remove("highlight", "1.0", tk.END)
            # Start searching from the beginning.
            self.last_found_index = "1.0"
            pos = self.txt.search(self.search_term, self.last_found_index, stopindex=tk.END)
            if pos:
                # Highlight the found text.
                end_pos = f"{pos}+{len(self.search_term)}c"
                self.txt.tag_add("highlight", pos, end_pos)
                # Adjust the view to make the found text visible.
                self.txt.see(pos)
                # Store the ending position for finding the next match.
                self.last_found_index = end_pos
            else:
                messagebox.showinfo("Result", "No matches found.")
        return "break"  # Prevent the default behavior.


    def find_next(self, event=None):
        ''' Search for next occurrence of text in response text area (self.txt) '''
        if not self.search_term:
            return self.find_text()

        pos = self.txt.search(self.search_term, self.last_found_index, stopindex=tk.END)
        if pos:
            # Remove previous highlights so only the current match is highlighted.
            self.txt.tag_remove("highlight", "1.0", tk.END)
            end_pos = f"{pos}+{len(self.search_term)}c"
            self.txt.tag_add("highlight", pos, end_pos)
            self.txt.see(pos)
            # Update the last found index.
            self.last_found_index = end_pos
        else:
            messagebox.showinfo("Result", "No more matches found.")
            self.txt.tag_remove("highlight", "1.0", tk.END)
        return "break"  # Prevent the default behavior.


    def is_url(self, s: str) -> bool:
        s = s.strip()
        if not s:
            return False
        try:
            p = urllib.parse.urlparse(s)
            return p.scheme in ('http', 'https', 'ftp', 'ftps') and bool(p.netloc)
        except Exception:
            return False

    def open_selected_url(self, e=None):
        try:
            sel = self.txt.get("sel.first", "sel.last")
        except TclError:
            # No selection
            return
        if self.is_url(sel):
            webbrowser.open(sel)


    def delete_log(self, e=None):
        ''' User request to remove the log file '''
        result = messagebox.askokcancel("Log File",
                                        f"Delete {self.MyPath} ?")
        if result is True:
            os.remove(self.MyPath)
            messagebox.showinfo("Log File",
                                f"{self.MyPath} Removed.")

    # toplevel window
    def create_window(self, e=None):
        ''' Opens a toplevel window providing selections of pre-written prompts '''
        inx = 0  # index of list item
        items = []
        pdet = []
        sdet = ''
        filepath = "prompts/prompts.txt"

        toplevel = Toplevel(self)
        toplevel.title("DescAI Prompt Selector")

        # Configure grid for the toplevel
        toplevel.grid_columnconfigure(0, weight=1)
        toplevel.grid_columnconfigure(1, weight=1)
        toplevel.grid_columnconfigure(2, weight=1)
        toplevel.grid_rowconfigure(1, weight=1)

        def item_selected(e=None):
            nonlocal inx, pdet
            list_item = listbox.curselection()
            item = listbox.get(list_item[0])
            inx = list_item[0]  # save the index

            txt.delete("1.0", END)
            txt.insert(1.0, pdet[inx])  # the entire line

            root.clipboard_clear()
            root.clipboard_append(pdet[inx])  # the entire line

        def pick(which):
            nonlocal inx, pdet
            if which == 1:
                # replace query box with this prompt DETAIL
                self.query.delete("1.0", END)  # clear the Text widget
                self.query.insert(1.0, pdet[inx])  # fill the Text widget
            else: # button 2
                # append to query box Text
                cmb = self.query.get(1.0, "end-1c")
                cmb = cmb + pdet[inx]
                self.query.delete("1.0", END)  # clear the Text widget
                self.query.insert(1.0, cmb)  # fill the Text widget

        def editor():
            ''' Launch editor with prompts.txt file '''
            subprocess.Popen([self.MyEditor, "prompts/prompts.txt"])

        # Listbox (read-only, single selection)
        listbox = Listbox(toplevel, height=8)
        listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        listbox.bind("<<ListboxSelect>>", item_selected)

        txt = Text(toplevel, padx=4, height=5)
        txt.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=5, pady=5)

        # Read items from a text file (one item per line)

        if os.path.exists(filepath):
            try:

                with open(filepath, "r", encoding="utf-8") as fin:
                    for line in fin:
                        if line.rstrip() == "%%%":
                            if sdet != '':
                                pdet.append(sdet)  # append previous DETAIL
                                sdet = ''
                            items.append(fin.readline().rstrip())  # append (next) new ITEMS line
                        else:
                            sdet += line
                    pdet.append(sdet)  # append previous and LAST DETAIL

            except Exception as e:
                messagebox.showerror("Error", f"Failed to read {filepath}:\n{e}")
        else:
            messagebox.showinfo("Info", f"Items file not found: {filepath}. No items loaded.")

        for it in items:
            listbox.insert(END, it)

        # Buttons 1, 2 (capture selection) and 3 (close)
        btn1 = Button(toplevel, text="Fill", command=lambda: pick(1))
        btn2 = Button(toplevel, text="Append", command=lambda: pick(2))
        btn3 = Button(toplevel, text="Edit", command=editor)
        btn4 = Button(toplevel, text="Close", command=toplevel.destroy)

        btn1.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        btn2.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        btn3.grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        btn4.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

        toplevel.update_idletasks()
        toplevel.geometry("400x350")
        toplevel.minsize(300, 300)
        toplevel.attributes("-topmost", True)  # Keep on top of other windows

    def on_key_release(self, event=None):
        self.highlight()

    def on_click(self, event=None):
        self.after(10, self.highlight)  # Small delay to ensure cursor position updates

    def highlight(self):
        # Remove existing tags ///
        for tag in ["headings", "bold", "italic", "hrule", "code"]:
            self.txt.tag_remove(tag, "1.0", "end")

        # Get all text content
        content = self.txt.get("1.0", "end-1c")

        # Highlight headings (must be at start of line)
        for i, line in enumerate(content.split('\n'), 1):
            # Heading 1 (# Header)
            if re.match(r'^#\s', line):
                self.txt.tag_add("headings", f"{i}.0", f"{i}.{len(line)}")
            # Heading 2 (## Header)
            elif re.match(r'^##\s', line):
                self.txt.tag_add("headings", f"{i}.0", f"{i}.{len(line)}")
            # Heading 3 (### Header)
            elif re.match(r'^###\s', line):
                self.txt.tag_add("headings", f"{i}.0", f"{i}.{len(line)}")
            # Heading 4 (#### Header)
            elif re.match(r'^####\s', line):
                self.txt.tag_add("headings", f"{i}.0", f"{i}.{len(line)}")
             # Heading 5 (##### Header)
            elif re.match(r'^#####\s', line):
                self.txt.tag_add("headings", f"{i}.0", f"{i}.{len(line)}")
            # Horizontal rule
            elif re.match(r'^(---+|___+|\*\*\*+)$', line):
                self.txt.tag_add("hrule", f"{i}.0", f"{i}.{len(line)}")

        # Highlight inline elements in entire content

        # Inline code (`code`)
        for match in re.finditer(r'`(.*?)`', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.txt.tag_add("code", start_idx, end_idx)

        # Bold (**text** or __text__)
        for match in re.finditer(r'\*\*(.*?)\*\*', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.txt.tag_add("bold", start_idx, end_idx)

        # Italic (*text* or _text_)
        for match in re.finditer(r'(?<!\*)\*(?!\*)(.*?)\*(?!\*)', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.txt.tag_add("italic", start_idx, end_idx)


    def exit_program(self, e=None):
        ''' Only exit program without prompt if
            1. Ctrl-q was hit
            OR
            2. Both Text frames are empty '''
        resp = self.txt.get("1.0", END).strip()
        qury = self.query.get("1.0", END).strip()
        if resp == "" and qury == "":
            save_location()
            sys.exit()
        if e is None:  # ctrl-q avoids this message
            if messagebox.askokcancel('DescAI',
                                      'Confirm Exit app?') is False:
                return
        save_location()

#------------------------------------------------------------

# SAVE GEOMETRY INFO AND EXIT
def save_location(e=None):
    ''' executes at WM_DELETE_WINDOW event - see below
        Also called from self.exit_program.
        Save window geometry before destruction
    '''
    with open("winfo", "w") as fout:
        fout.write(root.geometry())
    root.destroy()

# get options that go into the window creation and title
config = configparser.ConfigParser()
config.read('options.ini')
MyTheme = config['Main']['theme']
MyModel = config['Main']['engine']

# define main window
MyTitle = apptitle + MyModel
root = Window(MyTitle, MyTheme, iconphoto="icon.png")

# change working directory to path for this file
p = os.path.realpath(__file__)
os.chdir(os.path.dirname(p))

# ACCESS GEOMETRY INFO
if os.path.isfile("winfo"):
    with open("winfo") as f:
        lcoor = f.read()
    root.geometry(lcoor.strip())
else:
    root.geometry("675x505") # WxH+left+top

root.protocol("WM_DELETE_WINDOW", save_location)  # TO SAVE GEOMETRY INFO
root.minsize(790, 325)  # width, height
Sizegrip(root).place(rely=1.0, relx=1.0, x=0, y=0, anchor='se')

Application(root)

root.mainloop()
