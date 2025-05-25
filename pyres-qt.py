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
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class WorkerSignals(QObject):
    log = Signal(str)
    progress = Signal(int)
    done = Signal()


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

        command = [
            "ffmpeg",
            "-i", self.file,
            "-c:v", "prores_ks",
            "-profile:v", str(self.profile),
            "-pix_fmt", "yuv422p10le",
            "-threads", str(self.thread_count),
            "-c:a", "copy",
            output_file
        ]

        self.signals.log.emit(f"\nOKAY LET'S GO!: {self.file}")
        self.signals.log.emit("LET'S DO THIS: " + " ".join(shlex.quote(arg) for arg in command))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in process.stdout:
                self.signals.log.emit(line.strip())

            process.wait()
            self.signals.log.emit(f"ALL DONE!: {output_file}")
        except Exception as e:
            self.signals.log.emit(f"FUCKED IT!: {str(e)}")
        self.signals.progress.emit(1)
        self.signals.done.emit()


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
                self.addItem(path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAJAMALAND Media PyRes")
        self.resize(800, 600)
        self.thread_pool = QThreadPool()
        self.files_to_process = 0

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        self.drop_list = DropListWidget()
        layout.addWidget(QLabel("DROP YER FILES BELOW OR CLICK 'OPEN FILES'"))
        layout.addWidget(self.drop_list)

        controls = QHBoxLayout()
        self.open_button = QPushButton("OPEN FILES")
        self.open_button.clicked.connect(self.open_files)
        controls.addWidget(self.open_button)

        self.codec_box = QComboBox()
        self.codec_box.addItems(["0 - PROXY", "1 - LT", "2 - STANDARD", "3 - HQ"])
        self.codec_box.setCurrentIndex(2)
        controls.addWidget(QLabel("PRORES PROFILE:"))
        controls.addWidget(self.codec_box)

        self.threaded_box = QCheckBox("MULTI-THREADED ENCODING")
        self.threaded_box.setChecked(True)
        controls.addWidget(self.threaded_box)

        self.convert_button = QPushButton("SEND IT!!!")
        self.convert_button.clicked.connect(self.start_conversion)
        controls.addWidget(self.convert_button)

        layout.addLayout(controls)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

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

        for file in files:
            signals = WorkerSignals()
            signals.log.connect(self.log)
            signals.progress.connect(self.update_progress)
            worker = FFmpegWorker(file, profile, threads, signals)
            self.thread_pool.start(worker)

    def update_progress(self, value):
        self.progress.setValue(self.progress.value() + value)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
