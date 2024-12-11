from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QTextEdit, QInputDialog

import sys, json, csv, subprocess, re,os
from PyQt6.QtCore import QProcess, QProcessEnvironment
from rotating_circle import RotatingCircleWidget



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

        self.rotating_circle = RotatingCircleWidget()
        self.rotating_circle.setVisible(False)

        # Insert the rotating circle into the layout
        self.rotating_circle.insert_into_layout(self.quality_seasons_episodes_layout)

        self.setLayout(self.layout)


        self.saved_programs, self.services_data = self.load_saved_programs()
        self.update_series_combo()
        self.series_combo.currentTextChanged.connect(self.update_url_field)
        self.seasons = {}
        self.season_combo.currentIndexChanged.connect(self.update_episodes)

    from PyQt6.QtCore import QProcess

    def get_button_clicked(self):
        season_number = self.season_combo.currentText()
        quality = self.quality_combo.currentText()
        season_number = ''.join(filter(str.isdigit, season_number))
        episode_text = self.episode_combo.currentText()
        episode_number = ''.join(filter(str.isdigit, episode_text))
        season_number = season_number.zfill(2)
        episode_number = episode_number.zfill(2)
        url = self.url_entry.text()

        if url:
            service_code = self.get_service_code(url)
            if service_code:
                # Construct the shell command
                shell_command = f"devine dl -q {quality} -w s{season_number}e{episode_number} {service_code} {url}"
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

                # Connect signals
                self.process.readyReadStandardOutput.connect(self.handle_output)
                self.process.readyReadStandardError.connect(self.handle_error)
                self.process.started.connect(self.on_process_started)  # Monitor process start
                self.process.finished.connect(self.on_process_finished)  # Monitor process finish

                self.process.start()

                if not self.process.waitForStarted():
                    self.output_text.append("Error: Failed to start the devine process.")
            else:
                self.output_text.setText("Error: Unable to determine the service code for the provided URL.")
        else:
            self.output_text.setText("Error: URL is empty. Please provide a valid URL.")

    def on_process_started(self):
        self.rotating_circle.setVisible(True)

        self.rotating_circle.start_rotation()
        print("Started")

    def on_process_finished(self, exitCode, exitStatus):
        self.rotating_circle.stop_rotation()
        print("Ended")
        # You can also add additional actions here if needed based on the exit status
        if exitStatus == QProcess.ExitStatus.NormalExit:
            print(f"Process exited normally with exit code {exitCode}")
        else:
            print(f"Process exited with an error (exit code {exitCode})")

    def handle_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        #self.output_text.append(output)

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
        services_data = {}
        try:
            with open("series_data.json", "r") as file:
                saved_programs = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            saved_programs = {}
        try:
            with open("/Users/williamcorney/Library/Application Support/devine/services.cfg", "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) == 2:
                        services_data[row[0]] = row[1]
        except FileNotFoundError:
            print("services.cfg file not found!")
        return saved_programs, services_data

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
        if title and url:
            service_code = self.get_service_code(url)
            if service_code:
                self.run_devine_dl(service_code, url)
            else:
                self.output_text.append("No service code found for the URL")
        else:
            self.output_text.append("No title or URL found for listing episodes.")

    def get_service_code(self, url):
        for service_code, base_url in self.services_data.items():
            if url.startswith(base_url):
                return service_code
        return None

    import subprocess

    import logging

    # Set up logging to write to /Users/williamcorney/log.txt
    logging.basicConfig(
        filename='/Users/williamcorney/log.txt',
        level=logging.DEBUG,  # You can change this to logging.INFO for less verbose output
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    def run_devine_dl(self, service_code, url):
        try:
            # Run the command and capture stdout and stderr
            result = subprocess.run(
                f"devine dl --list-titles {service_code} {url}",
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            # If the command runs successfully, process the output
            self.parse_and_display_output(result.stdout)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            # Log the error if the subprocess fails
            logging.error(f"Command failed with error: {e}")
            logging.error(f"stdout: {e.stdout}")
            logging.error(f"stderr: {e.stderr}")
            logging.error(f"Service Code: {service_code}, URL: {url}")
            # Optionally, you can also log the stack trace
            logging.exception("Exception occurred")
        except Exception as e:
            # Catch any other exceptions and log them
            logging.error(f"Unexpected error: {e}")
            logging.exception("Exception occurred")

    def parse_and_display_output(self, output):
        #self.output_text.append(output)
        self.seasons = self.parse_output(output)
        self.populate_seasons()

    def parse_output(self, output, verbose=True):
        lines = output.split('\n')  # Split the output into lines

        # Dictionaries to hold the data for each block
        seasons_block1 = {}
        seasons_block2 = {}

        # Block 1 Processing
        current_season = None
        for line in lines:
            line = line.lstrip(" │├└─")  # Clean up the line

            # Match for season information (e.g., "├── Season 1: 1 episodes")
            season_match1 = re.match(r"^\s*Season\s*(\d+):\s*(\d+)\s*episodes?", line)
            if season_match1:
                season_number = int(season_match1.group(1))
                number_of_episodes = int(season_match1.group(2))
                seasons_block1[season_number] = {'number_of_episodes': number_of_episodes, 'episodes': []}
                current_season = season_number

            # Match for episode information (e.g., "│   ├── 1. The Conspiracy to Murder")
            episode_match1 = re.match(r"^\s*(\d+)\.\s*(.+)", line)
            if episode_match1 and current_season is not None:
                episode_number = int(episode_match1.group(1))
                episode_title = episode_match1.group(2).strip()
                seasons_block1[current_season]['episodes'].append((episode_number, episode_title))

            # If the line matches "Episode {number}" without a title, add a dummy title
            episode_match_no_title = re.match(r"^\s*Episode\s*(\d+)", line)
            if episode_match_no_title and current_season is not None:
                episode_number = int(episode_match_no_title.group(1))
                # Add a dummy title for this episode
                dummy_title = f"Episode"
                seasons_block1[current_season]['episodes'].append((episode_number, dummy_title))

        # Block 2 Processing
        season_number = None
        for line in lines:
            line = line.lstrip(" │├└─")  # Clean up the line

            # Match for season information (e.g., "├── Season 1: 1 episodes")
            season_match2 = re.match(r"^\s*[├└]──\s*Season\s*(\d+):\s*(\d+)\s*episode(?:s)?", line, re.IGNORECASE)
            if season_match2:
                season_number = int(season_match2.group(1))
                num_episodes = int(season_match2.group(2))
                # Overwrite or add season data
                seasons_block2[season_number] = {'number_of_episodes': num_episodes, 'episodes': []}

            # Match for episode information (e.g., "├── Episode 3")
            episode_match2 = re.match(r"^\s*[├└]──\s*Episode\s*(\d+)", line, re.IGNORECASE)
            if episode_match2:
                episode_number = int(episode_match2.group(1))
                if season_number in seasons_block2:
                    # Add episode with None as a placeholder title if no title is available
                    seasons_block2[season_number]['episodes'].append((episode_number, None))
                else:
                    # If no season is found, do nothing (skip)
                    pass

            # Match for episode line with title (e.g., "│   ├── 1. The Conspiracy to Murder")
            episode_match3 = re.match(r"^\s*[\│├└]──\s*(\d+)\.\s*(.+)", line)
            if episode_match3:
                episode_number = int(episode_match3.group(1))
                episode_title = episode_match3.group(2).strip()
                if season_number in seasons_block2:
                    seasons_block2[season_number]['episodes'].append((episode_number, episode_title))

        # Merge dictionaries by comparing their sizes
        if len(seasons_block1) > len(seasons_block2):
            final_seasons = seasons_block1
        else:
            final_seasons = seasons_block2

        # Remove seasons that have no episodes
        seasons = {season: data for season, data in final_seasons.items() if data['episodes']}

        # Return the final seasons dictionary

        return seasons

    def populate_seasons(self):
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
