import tkinter as tk
from tkinter import ttk
from datetime import datetime
import sys
import os


# importing the model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.model import DiagnosisModel

# --- Constants for the Theme ---
BG_COLOR = "#F4F6F7"
HEADER_COLOR = "#1C2833"
USER_BUBBLE_COLOR = "#2980B9"
BOT_BUBBLE_COLOR = "#EAECEE"
TEXT_COLOR_DARK = "#212F3D"
TEXT_COLOR_LIGHT = "#FFFFFF"
INPUT_BG_COLOR = "#FFFFFF"
FONT_NAME = "Segoe UI"
PRIMARY_COLOR = "#2980B9"

class ChatbotApp:
    def __init__(self, root):
        self.model = DiagnosisModel()
        self.user_symptoms = []
        self.message_widgets = []
        self.root = root
        self.root.title("AI Diagnosis")
        self.root.geometry("800x650")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)
        self.root.minsize(550, 450)
        self._create_header()
        self._create_input_area()
        self._create_chat_area()
        self._create_suggestion_box()
        self.root.bind('<Configure>', self._on_resize)
        self.start_conversation()

    def _create_header(self):
        header_frame = tk.Frame(self.root, bg=HEADER_COLOR)
        header_frame.pack(fill=tk.X, ipady=12)
        tk.Label(header_frame, text="AI Diagnostic Assistant", font=(FONT_NAME, 16, "bold"), bg=HEADER_COLOR, fg=TEXT_COLOR_LIGHT).pack(padx=15, side=tk.LEFT)

    def _create_input_area(self):
        self.input_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)
        input_container = tk.Frame(self.input_frame, bg=INPUT_BG_COLOR, highlightthickness=1, highlightbackground="#D1D5DB")
        input_container.pack(fill=tk.X, expand=True, ipady=2)
        self.entry_var = tk.StringVar()
        self.user_entry = tk.Entry(input_container, textvariable=self.entry_var, font=(FONT_NAME, 12), relief=tk.FLAT, bg=INPUT_BG_COLOR, fg=TEXT_COLOR_DARK)
        self.user_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=9, padx=10)
        self.user_entry.bind("<Return>", self.handle_send)
        self.user_entry.bind("<KeyRelease>", self.update_suggestions)
        send_button = tk.Button(input_container, text="➤", font=(FONT_NAME, 14, "bold"), bg=PRIMARY_COLOR, fg="white", 
                                command=self.handle_send, relief=tk.FLAT, bd=0, activebackground="#1F618D", activeforeground="white")
        send_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2), pady=2)

    def _create_chat_area(self):
        self.chat_canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.chat_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5))
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        self.message_frame = tk.Frame(self.chat_canvas, bg=BG_COLOR)
        self.canvas_frame = self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")
        self.message_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)

    def _create_suggestion_box(self):
        self.suggestion_listbox = tk.Listbox(self.root, height=5, font=(FONT_NAME, 10), relief=tk.FLAT, 
                                            bg="#FFFFFF", highlightthickness=1, highlightbackground=HEADER_COLOR)
        self.suggestion_listbox.bind("<<ListboxSelect>>", self.select_suggestion)
    
    def on_canvas_configure(self, event=None):
        self.chat_canvas.itemconfig(self.canvas_frame, width=event.width)
        self._on_resize()

    def _on_resize(self, event=None):
        new_wraplength = self.chat_canvas.winfo_width() * 0.8
        for widget_info in self.message_widgets:
            widget_info['bubble'].configure(wraplength=int(new_wraplength))

    def _create_bubble(self, sender, message):
        is_user = (sender == "user")
        row_frame = tk.Frame(self.message_frame, bg=BG_COLOR)
        bubble_frame = tk.Frame(row_frame, bg=USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR)
        text_color = TEXT_COLOR_LIGHT if is_user else TEXT_COLOR_DARK
        wraplength = int(self.chat_canvas.winfo_width() * 0.8)
        message_label = tk.Label(bubble_frame, text=message, font=(FONT_NAME, 11), wraplength=wraplength, 
                                justify=tk.LEFT, bg=USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR, fg=text_color, padx=10, pady=5)
        self.message_widgets.append({'bubble': message_label})
        message_label.pack(side=tk.TOP, anchor='w')
        timestamp = datetime.now().strftime("%I:%M %p")
        time_color = "#B2DFDB" if is_user else "#757575"
        time_label = tk.Label(bubble_frame, text=timestamp, font=(FONT_NAME, 8), bg=USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR, fg=time_color)
        time_label.pack(side=tk.BOTTOM, anchor='e', padx=10, pady=(0, 5))
        if is_user:
            bubble_frame.pack(side=tk.RIGHT, padx=(50, 5), pady=5)
        else:
            bubble_frame.pack(side=tk.LEFT, padx=(5, 50), pady=5)
        row_frame.pack(fill=tk.X, pady=2)

    def add_to_chat(self, sender, message):
        self._create_bubble(sender, message)
        self.root.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def start_conversation(self):
        self.add_to_chat("bot", "Hello! I am your AI health assistant. Please tell me your main symptom to begin.")

    def handle_send(self, event=None):
        user_input = self.entry_var.get().strip()
        if not user_input:
            return
        self.add_to_chat("user", user_input)
        self.user_symptoms.append(user_input.lower())
        self.entry_var.set("")
        self.suggestion_listbox.place_forget()
        if len(self.user_symptoms) < 3:
            self.add_to_chat("bot", "Thank you. Can you tell me another symptom?")
        else:
            self.run_diagnosis()

    def run_diagnosis(self):
        self.add_to_chat("bot", "Thank you. Analyzing your symptoms...")
        self.root.update_idletasks()
        disease, _ = self.model.predict_disease(self.user_symptoms)

        if "Could not identify" in disease or "Not enough information" in disease:
            self.add_to_chat("bot", "I'm sorry, I couldn't determine a likely condition based on your symptoms. It's always best to consult a doctor.")
        else:
            
            description = self.model.scrape_disease_description(disease)
            precautions = self.model.get_precautions(disease)
            precautions_text = "\n".join([f" ▸ {p.strip()}" for p in precautions])

            
            diagnosis_report = (
                f"DIAGNOSIS:\n{disease}\n\n"
                f"SUMMARY:\n{description}\n\n"
                f"RECOMMENDED PRECAUTIONS:\n{precautions_text}"
            )

            
            self.add_to_chat("bot", diagnosis_report)
            
            
            self.add_to_chat("bot", "Disclaimer: I am an AI assistant. Please consult a professional doctor for an accurate diagnosis and treatment.")
        
        self.user_symptoms.clear()
        self.add_to_chat("bot", "You can start over by telling me a new symptom.")
        
    def update_suggestions(self, event=None):
        query = self.entry_var.get()
        if query:
            suggestions = self.model.get_symptom_suggestions(query)
            if suggestions:
                self.suggestion_listbox.delete(0, tk.END)
                for s in suggestions[:5]:
                    self.suggestion_listbox.insert(tk.END, s)
                x_pos = self.user_entry.winfo_x() + self.input_frame.winfo_x()
                y_pos = self.input_frame.winfo_y() - 10
                width = self.user_entry.winfo_width()
                self.suggestion_listbox.place(x=x_pos, y=y_pos, width=width, anchor='sw')
                return
        self.suggestion_listbox.place_forget()

    def select_suggestion(self, event=None):
        if self.suggestion_listbox.curselection():
            selected = self.suggestion_listbox.get(self.suggestion_listbox.curselection())
            self.entry_var.set(selected)
            self.suggestion_listbox.place_forget()
            self.handle_send()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()