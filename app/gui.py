import tkinter
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import sys
import os
import glob

try:
    from PIL import Image
    import tkintermapview
    from geopy.geocoders import Nominatim
except ImportError:
    print("Required libraries not found. Please run: pip install customtkinter Pillow tkintermapview geopy")
    sys.exit()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.model import DiagnosisModel

# --- Constants for Glassmorphic Theme ---
FONT_NAME = "Segoe UI"
ACCENT_COLOR = "#00A8E8"
ACTIVE_BUTTON_COLOR = "#0077B6"
TEXT_COLOR = "#EAEAEA"
TEXT_COLOR_LIGHT = "#EAEAEA"  # Added missing constant
MUTED_TEXT_COLOR = "#AAB8C2"
USER_BUBBLE_COLOR = "#005C4B"
BOT_BUBBLE_COLOR = "gray25"
FRAME_COLOR = ("#2A3942", "#2A3942")
CONTENT_COLOR = "#7092A5"  # Added missing constant

# --- Helper Class for Tooltips ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            # fallback when widget doesn't support "insert" bbox (e.g., Button)
            x, y = 0, 0
        x += self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y += self.widget.winfo_rooty() + 10
        self.tooltip = tkinter.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(self.tooltip, text=self.text, fg_color="#1E1E1E", text_color="white",
                            font=(FONT_NAME, 9), corner_radius=6, padx=8, pady=4)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None

# --- Main Application Controller ---
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jeevaka - AI Diagnostic Suite")
        self.root.geometry("1920x1080")
        self.root.minsize(950, 700)

        ctk.set_appearance_mode("dark")

        self.user_profile = {'name': '', 'age': '', 'city': ''}
        self.model = DiagnosisModel()
        self.image_references = []  # To hold all image references
        self.main_container = ctk.CTkFrame(root, fg_color="transparent")
        self.main_container.pack(fill=tkinter.BOTH, expand=True)

        self._create_background()
        self._create_navigation_menu()
        self._create_content_frames()
        self.show_main_menu()

    def _create_background(self):
        """Create a persistent background image that stays behind all widgets."""
        try:
            bg_image_path = os.path.join('assets', 'glass_background.png')
            bg_image = ctk.CTkImage(Image.open(bg_image_path), size=(1280, 720))
            
            # ✅ Always create background_label
            self.background_label = ctk.CTkLabel(self.main_container, image=bg_image, text="")
            self.background_label.place(relwidth=1.0, relheight=1.0)
            self.background_label.lower()  # Send to back
            self.image_references.append(bg_image)
            print("Background image loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load background image. {e}")
            # ✅ Create placeholder so attribute always exists
            self.background_label = ctk.CTkLabel(self.main_container, text="", fg_color="transparent")
            self.background_label.place(relwidth=1.0, relheight=1.0)
            try:
                self.background_label.lower()
            except Exception:
                pass

    def _create_navigation_menu(self):
        self.navigation_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(
            self.navigation_frame,
            text="Jeevaka AI",
            font=ctk.CTkFont(family=FONT_NAME, size=28, weight="bold"),
            fg_color="transparent"
        ).pack(pady=(0, 40))
        
        self.nav_buttons = {}
        nav_items = {"Profile": "profile_icon.png", "Chatbot": "chat_icon.png", "History": "history_icon.png"}

        for text, icon_file in nav_items.items():
            try:
                img = Image.open(os.path.join('assets', icon_file))
                new_height = 48
                new_width = int((new_height / 2) * 5)
                resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS
                img = img.resize((new_width, new_height), resample_filter)
                icon_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_width, new_height))
            except Exception:
                icon_image = None
            
            button = ctk.CTkButton(
                self.navigation_frame, image=icon_image, text="",
                fg_color=FRAME_COLOR, width=150, height=80,
                hover_color=ACTIVE_BUTTON_COLOR, corner_radius=15,
                command=lambda t=text: self.show_frame(f"{t}Frame")
            )
            button.pack(fill=tkinter.X, pady=10)
            self.nav_buttons[f"{text}Frame"] = button
            ToolTip(button, text)

        try:
            self.navigation_frame.lift()
        except Exception:
            pass

    def _create_content_frames(self):
        self.frames = {}
        for F in (ProfileFrame, ChatbotFrame, HistoryFrame):
            frame = F(parent=self.main_container, controller=self)
            self.frames[F.__name__] = frame

    def show_main_menu(self):
        for frame in self.frames.values():
            frame.place_forget()
        self.navigation_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        try:
            self.navigation_frame.lift()
        except Exception:
            pass

    def show_frame(self, frame_name):
        self.navigation_frame.place_forget()
        self.background_label.lower()

        frame = self.frames[frame_name]
        frame.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        if hasattr(frame, 'on_show'):
            frame.on_show()

# --- Base Frame ---
class BaseFrame(ctk.CTkFrame):
    def __init__(self, parent, controller, title):
        super().__init__(parent, fg_color="transparent") 
        self.controller = controller
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill=tkinter.X, pady=(10, 0), padx=20)

        back_button = ctk.CTkButton(header_frame, text="< Back to Menu", font=(FONT_NAME, 12), text_color=MUTED_TEXT_COLOR,
                                    fg_color="transparent", hover_color=FRAME_COLOR,
                                    command=self.controller.show_main_menu)
        back_button.pack(side=tkinter.LEFT)

        ctk.CTkLabel(header_frame, text=title, font=ctk.CTkFont(family=FONT_NAME, size=24, weight="bold")).pack(side=tkinter.LEFT, expand=True, padx=20)

# --- Profile Frame ---
class ProfileFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="Your Profile")
        container = ctk.CTkFrame(self, fg_color=FRAME_COLOR, corner_radius=15, border_width=1, border_color="gray40")
        container.pack(expand=True, padx=20, pady=20)
        
        fields = {"Name": "name", "Age": "age", "City": "city"}
        self.entries = {}
        for label_text, key in fields.items():
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill=tkinter.X, padx=40, pady=15, side=tkinter.TOP)
            ctk.CTkLabel(row, text=f"{label_text}:", font=ctk.CTkFont(family=FONT_NAME, size=14), width=50, anchor='w').pack(side=tkinter.LEFT)
            entry = ctk.CTkEntry(row, font=ctk.CTkFont(family=FONT_NAME, size=14), corner_radius=8, border_width=1)
            entry.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
            self.entries[key] = entry

        ctk.CTkButton(container, text="Save & Start Chat", font=ctk.CTkFont(family=FONT_NAME, size=14, weight="bold"),
                    fg_color=ACCENT_COLOR, hover_color="#0077B6", corner_radius=8, height=40,
                    command=self.save_profile).pack(pady=40, padx=40)
    
    def save_profile(self):
        for key, entry in self.entries.items():
            self.controller.user_profile[key] = entry.get().strip()
        messagebox.showinfo("Success", "Your profile has been saved.")
        self.controller.show_frame("ChatbotFrame")

    def on_show(self):
        for key, entry in self.entries.items():
            entry.delete(0, tkinter.END)
            entry.insert(0, self.controller.user_profile.get(key, ''))

# --- Chatbot Frame ---
class ChatbotFrame(BaseFrame):
    BOT_NAME = "Jeevaka"
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="Chatbot")
        self.user_symptoms, self.message_widgets = [], []
        self.conversation_state, self.user_name, self.user_city = "", "", ""
        self._create_widgets()
    
    def on_show(self):
        new_name = self.controller.user_profile.get('name')
        new_city = self.controller.user_profile.get('city')
        if (self.user_name != new_name) or (self.user_city != new_city) or not self.message_widgets:
            for widget in self.chat_scroll_frame.winfo_children():
                widget.destroy()
            self.message_widgets, self.user_symptoms = [], []
            self.user_name, self.user_city = new_name, new_city
            if not self.user_name:
                self.conversation_state = "awaiting_name"
            elif not self.user_city:
                self.conversation_state = "awaiting_location"
            else:
                self.conversation_state = "collecting_symptoms"
            self.start_conversation()

    def _create_widgets(self):
        chat_card = ctk.CTkFrame(self, fg_color=FRAME_COLOR, corner_radius=15, border_width=1, border_color="gray40")
        chat_card.pack(fill=tkinter.BOTH, expand=True, padx=20, pady=(0, 10))
        
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X, padx=20, pady=(0,10))
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.user_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your symptom here...", font=(FONT_NAME, 14), corner_radius=15, border_width=1)
        self.user_entry.grid(row=0, column=0, sticky="ew", ipady=10)
        self.user_entry.bind("<Return>", self.handle_send)

        send_button = ctk.CTkButton(self.input_frame, text="Send", font=(FONT_NAME, 14, "bold"), corner_radius=15, width=80, height=40, command=self.handle_send)
        send_button.grid(row=0, column=1, padx=(10, 0))
        
        self.chat_scroll_frame = ctk.CTkScrollableFrame(chat_card, fg_color="transparent")
        self.chat_scroll_frame.pack(fill=tkinter.BOTH, expand=True, padx=5, pady=5)
        self.chat_scroll_frame.grid_columnconfigure(0, weight=1)

    def _add_bubble(self, sender, message=None, map_city=None):
        is_user = (sender == "user")
        anchor = "e" if is_user else "w"
        
        bubble_frame = ctk.CTkFrame(self.chat_scroll_frame, fg_color=USER_BUBBLE_COLOR if is_user else BOT_BUBBLE_COLOR, corner_radius=12)
        
        if message:
            name_text = "You" if is_user else self.BOT_NAME
            name_color = "#99FF99" if is_user else ACCENT_COLOR
            ctk.CTkLabel(bubble_frame, text=name_text, font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"), text_color=name_color).pack(anchor='w', padx=12, pady=(8, 0))
        
        if message:
            text_color = TEXT_COLOR_LIGHT
            ctk.CTkLabel(bubble_frame, text=message, font=(FONT_NAME, 12), justify="left", wraplength=500, fg_color="transparent", text_color=text_color).pack(padx=10, pady=(0, 10))

        elif map_city:
            ctk.CTkLabel(bubble_frame, text=self.BOT_NAME, font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"), text_color=ACCENT_COLOR).pack(anchor='w', padx=12, pady=(8, 0))
            try:
                geolocator = Nominatim(user_agent="ai_diagnosis_app_final")
                location = geolocator.geocode(map_city)
                if location:
                    map_widget = tkintermapview.TkinterMapView(bubble_frame, width=350, height=175, corner_radius=8)
                    map_widget.set_position(location.latitude, location.longitude)
                    map_widget.set_marker(location.latitude, location.longitude, text=map_city)
                    map_widget.set_zoom(11)
                    map_widget.pack(padx=5, pady=5)
                else:
                    self.after(0, lambda: self._add_bubble("bot", f"Sorry, I couldn't find a map for {map_city}."))
            except Exception as e:
                print(f"Map Error: {e}")
                self.after(0, lambda: self._add_bubble("bot", "Map service is currently unavailable."))
        
        bubble_frame.pack(anchor=anchor, padx=10, pady=5, ipadx=5, ipady=2, side=tkinter.TOP)
        self.after(100, lambda: getattr(self.chat_scroll_frame, "_parent_canvas", None) and self.chat_scroll_frame._parent_canvas.yview_moveto(1.0))
    
    def start_conversation(self):
        if self.conversation_state == "awaiting_name":
            self._add_bubble("bot", f"Hello! I'm {self.BOT_NAME}. To get started, what is your name?")
        elif self.conversation_state == "awaiting_location":
            self._add_bubble("bot", f"Nice to meet you, {self.user_name}! Now, please tell me your city.")
        elif self.conversation_state == "collecting_symptoms":
            self._add_bubble("bot", f"Welcome back, {self.user_name} from {self.user_city}. How may I assist you today?")
            self._add_bubble("bot", map_city=self.user_city)
            self._add_bubble("bot", "Please tell me your first symptom. When you're ready, type 'diagnose'.")
            
    def handle_send(self, event=None):
        user_input = self.user_entry.get().strip()
        if not user_input:
            return
        self._add_bubble("user", user_input)
        self.user_entry.delete(0, tkinter.END)
        
        if self.conversation_state == "awaiting_name":
            self.user_name = user_input.capitalize()
            self.controller.user_profile['name'] = self.user_name
            self.conversation_state = "awaiting_location"
            self.start_conversation()
        elif self.conversation_state == "awaiting_location":
            self.user_city = user_input.capitalize()
            self.controller.user_profile['city'] = self.user_city
            self.conversation_state = "collecting_symptoms"
            self.start_conversation()
        elif self.conversation_state == "collecting_symptoms":
            if 'diagnose' in user_input.lower():
                self.run_diagnosis()
            else:
                self.user_symptoms.append(user_input.lower())
                self._add_bubble("bot", "Symptom noted. You can add another or type 'diagnose' to proceed.")

    def run_diagnosis(self):
        if not self.user_symptoms:
            self._add_bubble("bot", "Please provide a symptom.")
            return
        self._add_bubble("bot", "Analyzing...")
        self.after(100, self._perform_diagnosis)

    def _perform_diagnosis(self):
        report = self.controller.model.get_ai_diagnosis(self.user_symptoms)
        self._add_bubble("bot", report)
        self._save_report(report)
        self._add_bubble("bot", "Disclaimer: This is an AI assistant, not a doctor.")
        self.user_symptoms.clear()

    def _save_report(self, report):
        try:
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(reports_dir, f"report_{self.user_name}_{timestamp}.txt")
            symptom_list = "\n- ".join(self.user_symptoms)
            report_content = (
                f"AI DIAGNOSIS REPORT\n"
                f"=====================\n"
                f"User: {self.user_name}\n"
                f"Location: {self.user_city}\n"
                f"Date: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n\n"
                f"Provided Symptoms:\n- {symptom_list}\n\n"
                f"--- AI ANALYSIS ---\n{report}\n\n"
                f"--- END OF REPORT ---\n"
            )
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report_content)
            self._add_bubble("bot", f"A copy of this report has been saved as {filename}")
        except Exception as e:
            self._add_bubble("bot", f"Error saving report: {e}")

# --- History Frame ---
class HistoryFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="History")
        self.history_listbox = None
        self.details_text = None
        self._create_widgets()

    def _create_widgets(self):
        history_card = ctk.CTkFrame(self, fg_color=FRAME_COLOR, corner_radius=15, border_width=1, border_color="gray40")
        history_card.pack(fill=tkinter.BOTH, expand=True, padx=20, pady=20)
        
        self.history_listbox = ctk.CTkScrollableFrame(history_card, fg_color="transparent", width=250)
        self.history_listbox.pack(side=tkinter.LEFT, fill=tkinter.Y, padx=(10, 5), pady=10)

        self.details_text = ctk.CTkTextbox(history_card, wrap="word", font=(FONT_NAME, 12))
        self.details_text.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=(5, 10), pady=10)

    def on_show(self):
        for widget in self.history_listbox.winfo_children():
            widget.destroy()
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            self.details_text.delete("1.0", tkinter.END)
            self.details_text.insert(tkinter.END, "No history found.")
            return
        report_files = sorted(glob.glob(os.path.join(reports_dir, "report_*.txt")), reverse=True)
        if not report_files:
            self.details_text.delete("1.0", tkinter.END)
            self.details_text.insert(tkinter.END, "No history found.")
            return
        for file_path in report_files:
            filename = os.path.basename(file_path)
            btn = ctk.CTkButton(self.history_listbox, text=filename, fg_color="transparent", hover_color=FRAME_COLOR,
                            command=lambda fp=file_path: self._show_report(fp))
            btn.pack(fill=tkinter.X, padx=5, pady=2)

    def _show_report(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.details_text.delete("1.0", tkinter.END)
            self.details_text.insert(tkinter.END, content)
        except Exception as e:
            self.details_text.delete("1.0", tkinter.END)
            self.details_text.insert(tkinter.END, f"Error reading file: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    root = ctk.CTk()
    app = MainApp(root)
    root.mainloop()
