from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QTextEdit, QInputDialog
from PyQt6.QtCore import QProcess, QProcessEnvironment
import sys, json, csv, subprocess, re,os,logging
from parsing import parse_season_data
from services import get_service_code
# from rotating_circle import RotatingCircleWidget
class DevineApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DEVINE")
        self.setFixedSize(1000, 600)
        self.layout = QVBoxLayout()
        self.selected_season = None
        self.series_combo = QComboBox(self)
        self.layout.addWidget(self.series_combo)
        self.url_row_layout = QHBoxLayout()
        self.url_label = QLabel("URL:", self)
        self.url_row_layout.addWidget(self.url_label)
        self.url_entry = QLineEdit(self)
        self.url_entry.setPlaceholderText("Enter URL here...")
        self.url_row_layout.addWidget(self.url_entry)
        self.layout.addLayout(self.url_row_layout)
        self.series_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Series", self)
        self.add_button.clicked.connect(self.add_series)
        self.series_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove Series", self)
        self.remove_button.clicked.connect(self.remove_series)
        self.series_layout.addWidget(self.remove_button)
        self.layout.addLayout(self.series_layout)
        self.quality_seasons_episodes_layout = QHBoxLayout()
        self.quality_label = QLabel("Quality:", self)
        self.quality_seasons_episodes_layout.addWidget(self.quality_label)
        self.quality_combo = QComboBox(self)
        self.quality_combo.addItems(["720p", "1080p"])
        self.quality_seasons_episodes_layout.addWidget(self.quality_combo)
        self.season_label = QLabel("Season:", self)
        self.quality_seasons_episodes_layout.addWidget(self.season_label)
        self.season_combo = QComboBox(self)
        self.quality_seasons_episodes_layout.addWidget(self.season_combo)
        self.episode_label = QLabel("Episode:", self)
        self.quality_seasons_episodes_layout.addWidget(self.episode_label)
        self.episode_combo = QComboBox(self)
        self.quality_seasons_episodes_layout.addWidget(self.episode_combo)
        self.layout.addLayout(self.quality_seasons_episodes_layout)
        self.console_label = QLabel("Console Output:", self)
        self.layout.addWidget(self.console_label)
        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.layout.addWidget(self.output_text)
        self.get_button = QPushButton("Get Episode", self)
        self.layout.addWidget(self.get_button)
        self.list_button = QPushButton("List Episodes", self)
        self.stop_button = QPushButton("Abort!",self)
        self.stop_button.clicked.connect (self.kill_process)
        self.list_button.clicked.connect(self.list_button_clicked)
        self.get_button.clicked.connect(self.get_button_clicked)
        self.layout.addWidget(self.list_button)
        self.layout.addWidget(self.stop_button)
        # self.rotating_circle = RotatingCircleWidget()
        # self.rotating_circle.setVisible(False)
        # # Insert the rotating circle into the layout
        # self.rotating_circle.insert_into_layout(self.quality_seasons_episodes_layout)
        self.setLayout(self.layout)
        self.saved_programs = self.load_saved_programs()
        self.update_series_combo()
        self.series_combo.currentTextChanged.connect(self.update_url_field)
        self.seasons = {}
        self.season_combo.currentIndexChanged.connect(self.update_episodes)

    # Configure the logger
    logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

    def get_button_clicked(self):
        season_number = self.season_combo.currentText()
        quality = self.quality_combo.currentText()
        season_number = ''.join(filter(str.isdigit, season_number))
        episode_text = self.episode_combo.currentText()
        episode_number = ''.join(filter(str.isdigit, episode_text))
        season_number = season_number.zfill(2)
        episode_number = episode_number.zfill(2)
        url = self.url_entry.text()

        # Log the input values
        logging.info(f"Season Number: {season_number}")
        logging.info(f"Episode Number: {episode_number}")
        logging.info(f"Quality: {quality}")
        logging.info(f"URL: {url}")

        if url:
            service_code = get_service_code(url)
            if service_code:
                # Construct the shell command
                shell_command = f"devine dl -q {quality} -w s{season_number}e{episode_number} {service_code} {url}"
                logging.info(f"Shell Command: {shell_command}")
                print(f"Shell: {shell_command}")
                self.process = QProcess(self)

                # Modify the PATH environment variable
                process_env = QProcessEnvironment.systemEnvironment()
                additional_path = "/Users/williamcorney/Library/Application Support/devine/"
                current_path = process_env.value("PATH")
                new_path = f"{additional_path}:{current_path}"
                process_env.insert("PATH", new_path)
                self.process.setProcessEnvironment(process_env)

                self.process.setProgram("/bin/bash")  # Use an interactive shell
                self.process.setArguments(["-c", shell_command])  # Pass the command as an argument to the shell

                # # Connect signals
                # self.process.readyReadStandardOutput.connect(self.handle_output)
                # self.process.readyReadStandardError.connect(self.handle_error)
                self.process.started.connect(self.on_process_started)  # Monitor process start
                self.process.finished.connect(self.on_process_finished)  # Monitor process finish

                self.process.start()

                if not self.process.waitForStarted():
                    self.output_text.append("Error: Failed to start the devine process.")
                    logging.error("Error: Failed to start the devine process.")
            else:
                self.output_text.setText("Error: Unable to determine the service code for the provided URL.")
                logging.error("Error: Unable to determine the service code for the provided URL.")
        else:
            self.output_text.setText("Error: URL is empty. Please provide a valid URL.")
            logging.error("Error: URL is empty. Please provide a valid URL.")

    def on_process_started(self):
        # self.rotating_circle.setVisible(True)
        #
        # self.rotating_circle.start_rotation()
        print("Started")

    def on_process_finished(self, exitCode, exitStatus):
        # self.rotating_circle.stop_rotation()
        print("Ended")
        # You can also add additional actions here if needed based on the exit status
        if exitStatus == QProcess.ExitStatus.NormalExit:
            print(f"Process exited normally with exit code {exitCode}")
        else:
            print(f"Process exited with an error (exit code {exitCode})")

    # def handle_output(self):
    #     output = self.process.readAllStandardOutput().data().decode()
    #     #self.output_text.append(output)

    def handle_error(self):
        error = self.process.readAllStandardError().data().decode()
        self.output_text.append(f"Error: {error}")

    def kill_process(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()  # Immediately kill the process
            print("Process killed")
        else:
            print("No running process to kill.")

    def load_saved_programs(self):
        saved_programs = {}

        try:
            with open("/Users/williamcorney/PycharmProjects/Devine3/series_data.json"
                      ""
                      "", "r") as file:
                saved_programs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            saved_programs = {}

        return saved_programs

    def update_series_combo(self):
        self.series_combo.clear()
        for title in self.saved_programs:
            self.series_combo.addItem(title)
        if self.series_combo.count() > 0:
            selected_title = self.series_combo.currentText()
            self.url_entry.setText(self.saved_programs.get(selected_title, ''))

    def update_url_field(self):
        selected_title = self.series_combo.currentText()
        if selected_title:
            self.url_entry.setText(self.saved_programs.get(selected_title, ''))

    def add_series(self):
        url = self.url_entry.text()
        title, ok = QInputDialog.getText(self, "Add Series", "Enter the title of the series:")
        if title and url:
            self.saved_programs[title] = url
            with open("series_data.json", "w") as file:
                json.dump(self.saved_programs, file, indent=4)
            self.update_series_combo()

    def remove_series(self):
        title = self.series_combo.currentText()
        if title:
            del self.saved_programs[title]
            with open("series_data.json", "w") as file:
                json.dump(self.saved_programs, file, indent=4)
            self.update_series_combo()
            self.url_entry.clear()

    def list_button_clicked(self):
        title = self.series_combo.currentText()
        url = self.url_entry.text()

        # Check if title or URL is missing
        if not title or not url:
            self.output_text.append("No title or URL found for listing episodes.")
            return

        # Check for service code
        service_code = get_service_code(url)
        if not service_code:
            self.output_text.append("No service code found for the URL.")
            return

        # Proceed if everything is valid
        self.run_devine_dl(service_code, url)

    def run_devine_dl(self, service_code, url):
        try:
            # Define the command as a list of arguments (avoiding shell=True)
            command = ["devine", "dl", "--list-titles", service_code, url]

            # Open a log file to capture the devine command output
            with open("example1.txt", "w") as log_file:
                # Run the devine command and capture stdout and stderr
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Write devine command output to the log file
                log_file.write("=== Devine Command Output ===\n")
                log_file.write(result.stdout)

                self.seasons = parse_season_data(result.stdout)
                self.update_seasons()

        except subprocess.CalledProcessError as e:
            pass


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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DevineApp()
    window.show()
    sys.exit(app.exec())
