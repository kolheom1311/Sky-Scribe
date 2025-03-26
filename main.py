import tkinter
import customtkinter
import subprocess

def run_python_file(file_path):
    try:
        subprocess.run(["python", file_path], check=True)
    except subprocess.CalledProcessError as e:
        tkinter.messagebox.showerror("Error", f"Error: {e}")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # configure window
        self.title("Sky Scribe")
        self.geometry(f"{1100}x{580}")
        # create left frame for menu bar
        self.menu_frame = customtkinter.CTkFrame(self, width=180, corner_radius=0)
        self.menu_frame.pack(side="left", fill="y")
        # project name label
        self.project_name_label = customtkinter.CTkLabel(self.menu_frame, text="Sky Scribe", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.project_name_label.pack(padx=20, pady=(20, 10))
        # create menu buttons with text (without icons)
        self.create_menu_button("Home", self.show_home_content)
        self.create_menu_button("About", self.show_about_content)
        self.create_menu_button("Settings", self.show_settings_content)
        
        # content frame for main content
        self.content_frame = customtkinter.CTkFrame(self)
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        # initially show home content
        self.show_home_content()

    def create_menu_button(self, text, command):
        button = customtkinter.CTkButton(self.menu_frame, text=text, compound="left", command=command)
        button.pack(padx=20, pady=10)

    def show_home_content(self):
        # remove any existing widgets in content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # create buttons for Home section
        button_1 = customtkinter.CTkButton(self.content_frame, text="PPT Control", command=lambda: run_python_file("PPT.py"))
        button_1.pack(padx=20, pady=20)
        
        button_2 = customtkinter.CTkButton(self.content_frame, text="Sky Scribble", command=lambda: run_python_file("Scribble.py"))
        button_2.pack(padx=20, pady=20)

    def show_about_content(self):
        # remove any existing widgets in content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # add text for About section
        about_text = """Welcome to SkyScribe, a revolutionary software that transforms the way you interact with digital content. With SkyScribe, you can write in the air, and your strokes will appear seamlessly on a digital canvas.

Our innovative capture feature not only saves your work but also evaluates any mathematical expressions on the screen. Using Google Cloud Vision, we recognize handwritten text, while the Gemini API processes mathematical expressions and returns results directly in the terminal.

But that’s not all! SkyScribe also enables PPT control and annotation in the air, making presentations more interactive and engaging. Whether you're a student, educator, or professional, SkyScribe is designed to enhance creativity, productivity, and seamless digital interaction.

Join us in redefining the way we write, calculate, and present—in the air!"""
        about_label = customtkinter.CTkLabel(self.content_frame, text=about_text, wraplength=600)
        about_label.pack(padx=20, pady=20)

  
    def show_settings_content(self):
        # remove any existing widgets in content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create a label for the theme option
        theme_label = customtkinter.CTkLabel(self.content_frame, text="Theme:")
        theme_label.pack(padx=20, pady=10)
        
        # Define available theme options
        theme_options = ["System", "Light", "Dark"]
        
        # Create a dropdown menu for selecting themes
        theme_var = tkinter.StringVar(self.content_frame)
        theme_var.set(customtkinter.get_appearance_mode())  # Set initial selection to current theme
        theme_dropdown = customtkinter.CTkComboBox(self.content_frame, values=theme_options, variable=theme_var, command=lambda: change_theme(theme_var.get()))
        theme_dropdown.pack(padx=20, pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
