#                   @@@@%%########%%%@@@@                     
#               @@##*******************##@@                  
#           @@@****************************#@@               
#         @@#*********************************%@@            
#       @@#*************************************#@@          
#      @%*************************#@@@@@%*********@@         
#     @%************%#************@@%@@@@@*********%@        
#    @#**%%*******%%**************@@@@@%@@**********%@   @@@@
#   @%*****#%#**#%#***************#@@@@@@#**********#@@%#*@@ 
#   @*********%@@******************************#@@@**+++#@           PAJAMALAND REZZER VER 0.2
#  @@*********%%*#@%##******************###@@#+++++@*+*@             CREATED BY PAJAMALAND MEDIA/PAJAMALAND DIGITAL STUDIO (https://pajamaland.tv/)
#  @%********%#********##*********#%@%@%*+++#*++++++@%@@             LICENCED UNDER THE GNU GENERAL PUBLIC LICENCE VERSION 3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
#  @@*******%#***************%@@##*++++++++++%*+++++@%@@             COMMERCIAL RE-DISTRIBUTION OF THIS SOFTWARE IS STRICTLY PROHIBITED.
#   @*****************#@@@#*+++#*+++++++++++++##++@%*#@
#   @%******####@@@#*+++++++++++%*+++++++++++++*@@#**%@      
#   @@%%%%%#**++#*+++++++++++++++%#+++++++++++%@#***#@       
# @%#*++++++++++++%*+++++++++++++++##+++++++*%@#****%@        
#  @@@*+++++++++++@*+++++++++++++++##++++*@%******@@         
#    @@@%#*+++++++#%+++++++++++++++%**%@#******#@@          
#         @@@@@%*+++*%*++++++++++++#@@#*******%@@            
#           @@@*#%@@%*#%+++++++*@@%#*******#@@@              
#               @@#***##%@@@@@#*********#@@                  
#                  @@@@%###########%@@@@                     

import sys
import os
import platform
import shlex
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton,
    QFileDialog, QHBoxLayout, QComboBox, QProgressBar, QTextEdit, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QThreadPool, QRunnable, Signal, QObject
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon

# --- grab resources ---
def resource_path(rel_path):
    if hasattr(sys, "_MEIPASS"):  # when bundled as an .exe
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.abspath(rel_path)  # otherwise just find it normally

# i hate windows so much
if platform.system() == "Windows":
    import ctypes
    myappid = u"pajamaland.rezzer.app"  # totally made up, but M$ likes IDs
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# threads --> main communication via signals
class WorkerSignals(QObject):
    log = Signal(str)
    progress = Signal(int)
    done = Signal()

# ffmpeg time babeyyyyy
class FFmpegWorker(QRunnable):
    def __init__(self, file, profile, thread_count, signals):
        super().__init__()
        self.file = file
        self.profile = profile
        self.signals = signals
        self.thread_count = thread_count

    def run(self):
        dirname, filename = os.path.split(self.file)
        name, _ = os.path.splitext(filename)
        output_file = os.path.join(dirname, f"{name}_prores.mov")

        # ffmpeg summoning circle
        command = [
            "ffmpeg",
            "-i", self.file,
            "-c:v", "prores_ks",
            "-profile:v", str(self.profile),
            "-pix_fmt", "yuv422p10le",
            "-threads", str(self.thread_count),
            "-c:a", "copy",  # just copies audio -- does NOT touch it
            output_file
        ]

        self.signals.log.emit(f"\nOKAY LET'S GO!: {self.file}")
        self.signals.log.emit("LET'S DO THIS: " + " ".join(shlex.quote(arg) for arg in command))

        try:
            # run ffmpeg (verbose)
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in process.stdout:
                self.signals.log.emit(line.strip())  # spew logs straight into the main window

            process.wait()
            self.signals.log.emit(f"ALL DONE!: {output_file}")
        except Exception as e:
            self.signals.log.emit(f"FUCKED IT!: {str(e)}")  # True and Honest((TM) Error Logging
        self.signals.progress.emit(1)  # tell progress bar we’re done with one file
        self.signals.done.emit()


# drag-and-drop list widget, so you can just shove shit in
class DropListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).is_file():
                self.addItem(path)  # boom, file added


# main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAJAMALAND Rezzer")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.resize(800, 600)
        self.thread_pool = QThreadPool()  # so we can do multiple files at once
        self.files_to_process = 0

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        self.drop_list = DropListWidget()
        layout.addWidget(QLabel("DROP YER FILES BELOW OR CLICK 'OPEN FILES'"))
        layout.addWidget(self.drop_list)

        # remove shit
        remove_button = QPushButton("REMOVE SELECTED")
        remove_button.clicked.connect(self.remove_selected)
        layout.addWidget(remove_button)

        # some controls for codec + threading options
        controls = QHBoxLayout()
        self.open_button = QPushButton("OPEN FILES")
        self.open_button.clicked.connect(self.open_files)
        controls.addWidget(self.open_button)

        self.codec_box = QComboBox()
        self.codec_box.addItems(["0 - PROXY", "1 - LT", "2 - STANDARD", "3 - HQ"])
        self.codec_box.setCurrentIndex(2)  # STANDARD by default
        controls.addWidget(QLabel("PRORES PROFILE:"))
        controls.addWidget(self.codec_box)

        self.threaded_box = QCheckBox("MULTI-THREADED ENCODING")
        self.threaded_box.setChecked(True)  # default = faster is better
        controls.addWidget(self.threaded_box)

        layout.addLayout(controls)

        # go button
        self.convert_button = QPushButton("SEND IT!!!")
        self.convert_button.setStyleSheet("font-size: 20px; padding: 10px;")
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        # progress bar so you know it’s not frozen
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # output log/live feed of ffmpeg schizoposting
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        layout.addWidget(self.output_log)

        self.setCentralWidget(central)

    def log(self, message):
        self.output_log.append(message)

    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "SELECT VIDEO FILES")
        for f in files:
            self.drop_list.addItem(f)

    def remove_selected(self):
        for item in self.drop_list.selectedItems():
            self.drop_list.takeItem(self.drop_list.row(item))

    def start_conversion(self):
        files = [self.drop_list.item(i).text() for i in range(self.drop_list.count())]
        if not files:
            self.log("NO FILES TO CONVERT!!!")
            return

        profile = self.codec_box.currentIndex()
        threads = os.cpu_count() if self.threaded_box.isChecked() else 1

        self.progress.setMaximum(len(files))
        self.progress.setValue(0)
        self.files_to_process = len(files)

        # spin up a worker thread for each file
        for file in files:
            signals = WorkerSignals()
            signals.log.connect(self.log)
            signals.progress.connect(self.update_progress)
            worker = FFmpegWorker(file, profile, threads, signals)
            self.thread_pool.start(worker)

    def update_progress(self, value):
        # bump progress bar along by whatever the worker says
        self.progress.setValue(self.progress.value() + value)


# standard “if you run this file directly” entrypoint
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
