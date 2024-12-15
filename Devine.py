from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QTextEdit, QInputDialog
from PyQt6.QtCore import QProcess, QProcessEnvironment
import sys, json, csv, subprocess, re,os
from parsing import parse_season_data
from services import get_service_code
# from rotating_circle import RotatingCircleWidget
class DevineApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DEVINE")
        self.setFixedSize(1000, 600)
        self.seasons = {}
        self.layout = QVBoxLayout()
        self.url_row_layout = QHBoxLayout()
        self.series_layout = QHBoxLayout()
        self.quality_seasons_episodes_layout = QHBoxLayout()
        self.series_combo = QComboBox()
        self.url_entry = QLineEdit()
        self.url_label = QLabel("URL:")
        self.remove_button = QPushButton("Remove Series")
        self.layout.addWidget(self.series_combo)
        self.quality_label = QLabel("Quality:")
        self.episode_label = QLabel("Episode:")
        self.quality_combo = QComboBox()
        self.season_label = QLabel("Season:")

        self.abort_button = QPushButton("Abort!")
        self.clear_env_button = QPushButton("Clear Environment")
        self.download_button = QPushButton("Get Episode")
        self.add_button = QPushButton("Add Series")
        self.url_row_layout.addWidget(self.url_label)
        self.episode_combo = QComboBox(self)
        self.list_button = QPushButton("List Episodes")
        self.process = QProcess(self)
        self.output_text = QTextEdit(self)
        self.season_combo = QComboBox(self)
        self.url_row_layout.addWidget(self.url_entry)
        self.series_layout.addWidget(self.add_button)
        self.series_layout.addWidget(self.remove_button)
        self.quality_seasons_episodes_layout.addWidget(self.quality_label)
        self.quality_seasons_episodes_layout.addWidget(self.quality_combo)
        self.quality_seasons_episodes_layout.addWidget(self.season_label)
        self.quality_seasons_episodes_layout.addWidget(self.season_combo)
        self.quality_seasons_episodes_layout.addWidget(self.episode_label)
        self.quality_seasons_episodes_layout.addWidget(self.episode_combo)

        self.layout.addLayout(self.url_row_layout)
        self.layout.addLayout(self.series_layout)
        self.layout.addLayout(self.quality_seasons_episodes_layout)
        self.layout.addWidget(self.output_text)
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.list_button)
        self.layout.addWidget(self.abort_button)
        self.layout.addWidget(self.clear_env_button)
        self.setLayout(self.layout)

        self.download_button.clicked.connect(self.download_episodes)
        self.series_combo.currentTextChanged.connect(self.update_url_field)
        self.season_combo.currentIndexChanged.connect(self.update_episodes)
        self.add_button.clicked.connect(self.add_series)
        self.remove_button.clicked.connect(self.remove_series)
        self.abort_button.clicked.connect (self.kill_process)
        self.list_button.clicked.connect(self.list_clicked)
        self.clear_env_button.clicked.connect(self.clear_env_button_clicked)

        self.quality_combo.addItems(["720p", "1080p"])
        self.url_entry.setPlaceholderText("Enter URL here...")
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.list_button.setFocus()
        self.update_series()
        self.add_to_path()
        # self.rotating_circle = RotatingCircleWidget()
        # self.rotating_circle.setVisible(False)
        # # Insert the rotating circle into the layout
        # self.rotating_circle.insert_into_layout(self.quality_seasons_episodes_layout)

    def list_clicked(self):
        title = self.series_combo.currentText()
        url = self.url_entry.text()
        if not title or not url:
            self.output_text.append("No title or URL found for listing episodes.")
        self.service_code = get_service_code(url)
        #print (self.service_code)
        if not self.service_code:
            self.output_text.append("No service code found for the URL.")
            return
        command = ["devine", "dl", "--list-titles", self.service_code, url]
        #print (command)
        result = subprocess.run(command,capture_output=True,text=True,check=True)
        self.seasons = parse_season_data(result.stdout)
        self.update_seasons()


    def update_seasons(self):
        self.season_combo.clear()
        for season in self.seasons:
            self.season_combo.addItem(f"Season {season}")

    def update_episodes(self):
        self.episode_combo.clear()
        season_text = self.season_combo.currentText()

        if season_text:
            season_number = int(season_text.split()[-1])
            if season_number in self.seasons:
                episodes = self.seasons[season_number]['episodes']
                for episode_number, episode_title in episodes:
                    self.episode_combo.addItem(f"{episode_number}. {episode_title}")

    def download_episodes(self):
        season_number = self.season_combo.currentText()
        quality = self.quality_combo.currentText()
        season_number = ''.join(filter(str.isdigit, season_number))
        episode_text = self.episode_combo.currentText()
        episode_number = ''.join(filter(str.isdigit, episode_text))
        season_number = season_number.zfill(2)
        episode_number = episode_number.zfill(2)
        url = self.url_entry.text()

        if url:

            if self.service_code:
                # Construct the shell command
                shell_command = f"devine dl -q {quality} -w s{season_number}e{episode_number} {self.service_code} {url}"
                #print(f"Shell: {shell_command}")

                process_env = QProcessEnvironment.systemEnvironment()
                additional_path = "/Users/williamcorney/Library/Application Support/devine/"
                current_path = process_env.value("PATH")
                new_path = f"{additional_path}:{current_path}"
                process_env.insert("PATH", new_path)
                self.process.setProcessEnvironment(process_env)

                self.process.setProgram("/bin/bash")  # Use an interactive shell
                self.process.setArguments(["-c", shell_command])  # Pass the command as an argument to the shell

                self.process.started.connect(self.on_process_started)  # Monitor process start
                self.process.finished.connect(self.on_process_finished)  # Monitor process finish

                self.process.start()

                if not self.process.waitForStarted():
                    self.output_text.append("Error: Failed to start the devine process.")
            else:
                self.output_text.setText("Error: Unable to determine the service code for the provided URL.")
        else:
            self.output_text.setText("Error: URL is empty. Please provide a valid URL.")

    def clear_env_button_clicked(self):
        #print ('test')
        shell_command = f"devine env clear temp & devine env clear cache"
        self.process.setArguments(["-c", shell_command])  # Pass the command as an argument to the shell
        self.process.start()
    def on_process_started(self):
        # self.rotating_circle.setVisible(True)
        #
        # self.rotating_circle.start_rotation()
        print("Started")

    def on_process_finished(self, exitCode, exitStatus):
        # self.rotating_circle.stop_rotation()
        print("Ended")


    def kill_process(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()  # Immediately kill the process
            print("Process killed")
        else:
            print("No running process to kill.")



    def update_url_field(self):
        selected_title = self.series_combo.currentText()
        if selected_title:
            self.url_entry.setText(self.saved_programs.get(selected_title, ''))

    def update_series(self):
        self.saved_programs = {}

        file_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "devine", "series_data.json")
        try:
            with open(file_path, "r") as file:
                self.saved_programs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.saved_programs = {}

        # Update the series combo box
        self.series_combo.clear()
        for title in self.saved_programs:
            self.series_combo.addItem(title)

        # Set the URL entry field for the currently selected series
        if self.series_combo.count() > 0:
            selected_title = self.series_combo.currentText()
            self.url_entry.setText(self.saved_programs.get(selected_title, ''))

    def add_series(self):
        url = self.url_entry.text()
        file_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "devine", "series_data.json")

        title, ok = QInputDialog.getText(self, "Add Series", "Enter the title of the series:")
        if title and url:
            self.saved_programs[title] = url
            with open(file_path, "w") as file:
                json.dump(self.saved_programs, file, indent=4)
            self.update_series_combo()

    def remove_series(self):
        file_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "devine", "series_data.json")

        title = self.series_combo.currentText()
        if title:
            del self.saved_programs[title]
            with open(file_path, "w") as file:
                json.dump(self.saved_programs, file, indent=4)
            self.update_series_combo()
            self.url_entry.clear()

    def update_series_combo(self):
        self.series_combo.clear()
        for title in self.saved_programs:
            self.series_combo.addItem(title)
        if self.series_combo.count() > 0:
            selected_title = self.series_combo.currentText()
            self.url_entry.setText(self.saved_programs.get(selected_title, ''))
    def add_to_path(self):
        # Define the directories to add to PATH
        directories_to_add = "/Users/williamcorney/perl5/bin:/opt/miniconda3/envs/pythonProject1/bin:/opt/miniconda3/condabin:/Users/williamcorney/Library/Python/3.9/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Library/Frameworks/Python.framework/Versions/3.10/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/zfs/bin:/Library/Apple/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin"

        # Get the current PATH
        current_path = os.environ.get('PATH', '')

        # Append the new directories to the current PATH
        new_path = current_path + ':' + directories_to_add
        os.environ['PATH'] = new_path
        print (os.environ['PATH'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DevineApp()
    window.show()
    sys.exit(app.exec())
