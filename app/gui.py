import tkinter as tk
from tkinter import ttk
from datetime import datetime
import sys
import os

try:
    import tkintermapview
    from geopy.geocoders import Nominatim
except ImportError:
    print("Required libraries not found. Please run: pip install Pillow tkintermapview geopy")
    sys.exit()

# importing the model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.model import DiagnosisModel

# --- Constants for the Modern Professional Theme ---
WINDOW_BG = "#F1F5F9"
CARD_BG = "#FFFFFF"
HEADER_BG = "#1E293B"
USER_BUBBLE_COLOR = "#3B82F6"
BOT_BUBBLE_COLOR = "#E2E8F0"
TEXT_COLOR_DARK = "#0F172A"
TEXT_COLOR_LIGHT = "#FFFFFF"
INPUT_BG_COLOR = "#F8FAFC"
FONT_NAME = "Segoe UI"
PRIMARY_COLOR = "#3B82F6" # Accent color for bot's name

class ChatbotApp:
    BOT_NAME = "Jeevaka"

    def __init__(self, root):
        self.model = DiagnosisModel()
        self.user_symptoms = []
        self.message_widgets = []
        
        self.conversation_state = "awaiting_name" 
        self.user_name = ""
        self.user_city = ""

        self.root = root
        self.root.title(f"{self.BOT_NAME} - AI Diagnostic Assistant")
        self.root.geometry("800x700")
        self.root.configure(bg=WINDOW_BG)
        self.root.resizable(True, True)
        self.root.minsize(600, 500)

        self._create_header()
        self._create_input_area()
        self._create_chat_area()
        self._create_suggestion_box()
        
        self.root.bind('<Configure>', self._on_resize)
        self.start_conversation()

    def _create_header(self):
        header_frame = tk.Frame(self.root, bg=HEADER_BG)
        header_frame.pack(fill=tk.X, ipady=12)
        tk.Label(header_frame, text=f"🩺 {self.BOT_NAME}", font=(FONT_NAME, 16, "bold"), bg=HEADER_BG, fg="white").pack(side=tk.LEFT, padx=15)

    def _create_input_area(self):
        self.input_frame = tk.Frame(self.root, bg=WINDOW_BG)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))
        
        input_bg_frame = tk.Frame(self.input_frame, bg=INPUT_BG_COLOR, borderwidth=1, relief="solid", highlightbackground="#CBD5E1", highlightthickness=1)
        input_bg_frame.pack(fill=tk.X, expand=True)

        self.entry_var = tk.StringVar()
        self.user_entry = tk.Entry(input_bg_frame, textvariable=self.entry_var, font=(FONT_NAME, 12),
                                relief=tk.FLAT, bg=INPUT_BG_COLOR, fg=TEXT_COLOR_DARK, insertbackground=TEXT_COLOR_DARK)
        self.user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=10)
        self.user_entry.bind("<Return>", self.handle_send)
        self.user_entry.bind("<KeyRelease>", self.update_suggestions)
        
        send_button = tk.Button(input_bg_frame, text="➤", bg=USER_BUBBLE_COLOR, fg="white", font=(FONT_NAME, 14, "bold"),
                                relief=tk.FLAT, bd=0, activebackground="#2563EB", activeforeground="white",
                                cursor="hand2", command=self.handle_send)
        send_button.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,1), pady=1)

    def _create_chat_area(self):
        chat_card = tk.Frame(self.root, bg=CARD_BG, bd=1, relief="solid", highlightbackground="#CBD5E1", highlightthickness=1)
        chat_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.chat_canvas = tk.Canvas(chat_card, bg=CARD_BG, highlightthickness=0)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        scrollbar = ttk.Scrollbar(chat_card, orient="vertical", command=self.chat_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.message_frame = tk.Frame(self.chat_canvas, bg=CARD_BG)
        self.canvas_frame = self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")

        self.message_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)

    def _create_suggestion_box(self):
        self.suggestion_listbox = tk.Listbox(self.root, height=5, font=(FONT_NAME, 10), relief=tk.FLAT,
                                            bg="#FFFFFF", highlightthickness=1, highlightbackground=HEADER_BG)
        self.suggestion_listbox.bind("<<ListboxSelect>>", self.select_suggestion)

    def on_canvas_configure(self, event=None):
        self.chat_canvas.itemconfig(self.canvas_frame, width=event.width)
        self._on_resize()

    def _on_resize(self, event=None):
        new_wraplength = self.chat_canvas.winfo_width() * 0.7
        for widget_info in self.message_widgets:
            if widget_info['type'] == 'text':
                widget_info['bubble'].configure(wraplength=int(new_wraplength))

    def _add_bubble(self, sender, message=None, map_city=None):
        is_user = (sender == "user")
        row_frame = tk.Frame(self.message_frame, bg=CARD_BG)
        
        bubble_color = USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR
        bubble_frame = tk.Frame(row_frame, bg=bubble_color)
        
        # --- Add the bot's name to its bubbles ---
        if not is_user:
            name_label = tk.Label(bubble_frame, text=self.BOT_NAME, font=(FONT_NAME, 10, "bold"),
                                bg=bubble_color, fg=PRIMARY_COLOR)
            name_label.pack(anchor='w', padx=12, pady=(8, 0))
        
        if message:
            text_color = TEXT_COLOR_LIGHT if is_user else TEXT_COLOR_DARK
            wraplength = int(self.chat_canvas.winfo_width() * 0.7)
            message_label = tk.Label(bubble_frame, text=message, font=(FONT_NAME, 11), wraplength=wraplength,
                                    justify=tk.LEFT, bg=bubble_color, fg=text_color, padx=12, pady=5)
            self.message_widgets.append({'bubble': message_label, 'type': 'text'})
            # Adjust padding if name is present
            message_label.pack(side=tk.TOP, anchor='w', pady=(0, 5) if not is_user else 5)
        
        elif map_city:
            try:
                geolocator = Nominatim(user_agent="ai_diagnosis_app_final_v2")
                location = geolocator.geocode(map_city)
                if location:
                    map_widget = tkintermapview.TkinterMapView(bubble_frame, width=350, height=175, corner_radius=0)
                    map_widget.set_position(location.latitude, location.longitude)
                    map_widget.set_marker(location.latitude, location.longitude, text=map_city)
                    map_widget.set_zoom(11)
                    map_widget.pack(padx=5, pady=5)
                    self.message_widgets.append({'bubble': map_widget, 'type': 'map'})
                else:
                    self._add_bubble("bot", f"Sorry, I couldn't find a map for {map_city}.")
            except Exception:
                self._add_bubble("bot", "Map service is currently unavailable.")
        
        timestamp = datetime.now().strftime("%I:%M %p")
        time_label = tk.Label(row_frame, text=timestamp, font=(FONT_NAME, 8), bg=CARD_BG, fg="#94A3B8")
        
        if is_user:
            bubble_frame.pack(side=tk.RIGHT, pady=2)
            time_label.pack(side=tk.LEFT, anchor='se', padx=5)
            row_frame.pack(fill=tk.X, padx=(40, 10), pady=5)
        else:
            bubble_frame.pack(side=tk.LEFT, pady=2)
            time_label.pack(side=tk.RIGHT, anchor='sw', padx=5)
            row_frame.pack(fill=tk.X, padx=(10, 40), pady=5)
            
        self.root.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def start_conversation(self):
        self._add_bubble("bot", f"Hello! I'm {self.BOT_NAME}, I'm here to assist you. What is your name?")

    def handle_send(self, event=None):
        user_input = self.entry_var.get().strip()
        if not user_input:
            return
        self.entry_var.set("")
        self.suggestion_listbox.place_forget()
        self._add_bubble("user", user_input)

        if self.conversation_state == "awaiting_name":
            self.user_name = user_input.capitalize()
            self._add_bubble("bot", f"Hello, {self.user_name}! Can you please tell me your city?")
            self.conversation_state = "awaiting_location"
        
        elif self.conversation_state == "awaiting_location":
            self.user_city = user_input.capitalize()
            self._add_bubble("bot", f"Nice to meet you, {self.user_name} from {self.user_city}.")
            self._add_bubble("bot", map_city=self.user_city)
            self._add_bubble("bot", "Now, please tell me your first symptom.")
            self.conversation_state = "collecting_symptoms"
        
        elif self.conversation_state == "collecting_symptoms":
            if 'diagnose' in user_input.lower():
                self.run_diagnosis()
            else:
                self.user_symptoms.append(user_input.lower())
                self._add_bubble("bot", "Symptom noted. You can add another or type 'diagnose' to proceed.")

    def run_diagnosis(self):
        if not self.user_symptoms:
            self._add_bubble("bot", "Please provide at least one symptom before asking for a diagnosis.")
            return
        self._add_bubble("bot", "Thank you. Analyzing your symptoms...")
        self.root.update_idletasks()
        disease, _ = self.model.predict_disease(self.user_symptoms)
        if "Could not identify" in disease or "Not enough information" in disease:
            self._add_bubble("bot", "I'm sorry, I couldn't determine a likely condition based on your symptoms.")
        else:
            description = self.model.scrape_disease_description(disease)
            precautions = self.model.get_precautions(disease)
            diagnosis_report = (f"DIAGNOSIS:\n{disease}\n\nSUMMARY:\n{description}\n\nRECOMMENDED PRECAUTIONS:\n" + "\n".join([f" ▸ {p.strip()}" for p in precautions]))
            self._add_bubble("bot", diagnosis_report)
            self._save_report(disease, description, "\n".join([f" ▸ {p.strip()}" for p in precautions]))
            self._add_bubble("bot", "Disclaimer: I am an AI assistant. Please consult a professional doctor for an accurate diagnosis.")
        self.user_symptoms.clear()
        self._add_bubble("bot", "You can start over by telling me a new symptom.")

    def _save_report(self, disease, description, precautions):
        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(reports_dir, f"report_{self.user_name}_{timestamp}.txt")
            report_content = (f"AI DIAGNOSIS REPORT\n=====================\nUser: {self.user_name}\nLocation: {self.user_city}\nDate: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n\nProvided Symptoms:\n- {'\n- '.join(self.user_symptoms)}\n\n--- AI ANALYSIS ---\nPossible Condition: {disease}\n\nSummary:\n{description}\n\nRecommended Precautions:\n{precautions}\n\n--- END OF REPORT ---\n")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report_content)
            self._add_bubble("bot", f"A copy of this report has been saved as:\n{os.path.abspath(filename)}")
        except Exception as e:
            print(f"Error saving report: {e}")
            self._add_bubble("bot", "There was an error saving your report.")

    def update_suggestions(self, event=None):
        if self.conversation_state != "collecting_symptoms":
            self.suggestion_listbox.place_forget()
            return
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