from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.clock import Clock
import requests
from bs4 import BeautifulSoup
import os
import threading

Window.size = (520, 420)
Window.clearcolor = (1, 1, 1, 1)

class FolderPicker(ModalView):
    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.9)
        self.filechooser = FileChooserIconView(path=os.getcwd(), filters=['*/'], dirselect=True)
        self.on_select = on_select
        box = BoxLayout(orientation='vertical')
        box.add_widget(self.filechooser)
        select_button = Button(text="Choose Folder", size_hint=(1, None), height=50)
        select_button.bind(on_press=self.select_folder)
        box.add_widget(select_button)
        self.add_widget(box)

    def select_folder(self, instance):
        selected = self.filechooser.selection
        if selected:
            self.on_select(selected[0])
            self.dismiss()

class Downloader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)

        self.download_folder = os.getcwd()

        self.add_widget(Label(text='📥 Pinterest Video Downloader', font_size=20, bold=True, color=(0,0,0,1)))

        self.url_input = TextInput(hint_text="Paste Pinterest video URL here...", multiline=False, size_hint=(1, None), height=40)
        self.add_widget(self.url_input)

        self.file_name_input = TextInput(hint_text="Enter file name (no extension)", multiline=False, size_hint=(1, None), height=40)
        self.add_widget(self.file_name_input)

        self.folder_label = Label(text=f"Save to: {self.download_folder}", size_hint=(1, None), height=30)
        self.add_widget(self.folder_label)

        self.browse_btn = Button(text="Browse Folder", size_hint=(1, None), height=45, background_color=(0.6, 0.6, 0.6, 1))
        self.browse_btn.bind(on_press=self.open_folder_picker)
        self.add_widget(self.browse_btn)

        self.download_btn = Button(text="Download", size_hint=(1, None), height=45, background_color=(0.1, 0.6, 0.2, 1))
        self.download_btn.bind(on_press=self.start_download)
        self.add_widget(self.download_btn)

        self.progress_bar = ProgressBar(max=100, value=0, size_hint=(1, None), height=20)
        self.add_widget(self.progress_bar)

        self.progress_label = Label(text="", size_hint=(1, None), height=30)
        self.add_widget(self.progress_label)

    def open_folder_picker(self, instance):
        picker = FolderPicker(on_select=self.set_download_folder)
        picker.open()

    def set_download_folder(self, folder_path):
        self.download_folder = folder_path
        self.folder_label.text = f"Save to: {self.download_folder}"

    def show_popup(self, title, message):
        popup = Popup(title=title,
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def get_video_url(self, pinterest_url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(pinterest_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            video_tag = soup.find("meta", property="og:video")
            if video_tag:
                return video_tag["content"]
        except Exception as e:
            print("Error:", e)
        return None

    def start_download(self, instance):
        self.progress_bar.value = 0
        self.progress_label.text = ""
        threading.Thread(target=self.download_video).start()

    def update_progress(self, percent, text):
        self.progress_bar.value = percent
        self.progress_label.text = text

    def download_video(self):
        url = self.url_input.text.strip()
        filename_input = self.file_name_input.text.strip()

        if not url:
            Clock.schedule_once(lambda dt: self.show_popup("Error", "Please enter a Pinterest video URL."))
            return

        if not filename_input:
            Clock.schedule_once(lambda dt: self.show_popup("Error", "Please enter a file name."))
            return

        video_url = self.get_video_url(url)
        if not video_url:
            Clock.schedule_once(lambda dt: self.show_popup("Error", "Could not extract video from the URL."))
            return

        try:
            full_path = os.path.join(self.download_folder, f"{filename_input}.mp4")
            response = requests.get(video_url, stream=True)
            total_length = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total_length) * 100)
                        Clock.schedule_once(lambda dt, p=percent: self.update_progress(p, f"Downloading: {p}%"))

            Clock.schedule_once(lambda dt: self.show_popup("Success", f"Saved as:\n{full_path}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("Error", f"Download failed:\n{e}"))

class PinterestApp(App):
    def build(self):
        self.title = "Pinterest Downloader (Windows)"
        return Downloader()

if __name__ == "__main__":
    PinterestApp().run()
