from progress.spinner import Spinner
from progress import SHOW_CURSOR
from multiprocessing import Process, Pipe
import time

# DONT LOOK AT THIS CODE, ITS A MESS AND I KNOW IT BUT IT WORKS SO I DONT CARE :D

class TDTKSpinner(Spinner):
    done = False

    def update(self):
        if not self.done:
            i = self.index % len(self.phases)
            message = self.message % self
            line = ''.join([message, self.phases[i]])
            self.writeln(line)

    def finish(self):
        # Hide progress bar
        self.done = True
        if self.file and self.is_tty():
            print(file=self.file)
            if self._hidden_cursor:
                print(SHOW_CURSOR, end='', file=self.file)
                self._hidden_cursor = False

    def stop(self):
        self.done = True
        self.finish()

class Indicator:
    def __init__(self) -> None:
        self.spinner = TDTKSpinner('')
        self.run = False
        self.process_started = False  # New flag to track whether the process is started
        self.parent_conn, self.child_conn = Pipe()
        self._process = Process(target=self.next, args=(self.child_conn,), daemon=True)

    def start(self):
        self.run = True
        self.spinner.done = False  # Reset the done attribute
        if not self.process_started:
            self._process.start()
            self.process_started = True
        else:
            self.parent_conn.send("start")

    def stop(self):
        self.spinner.done = True
        self.spinner.stop()
        self.run = False
        self.parent_conn.send("stop")

    def next(self, conn):
        while self.run:
            time.sleep(0.1)  # Adjust the sleep time based on your needs
            if not self.spinner.done:
                self.spinner.next()
            if conn.poll():  # Check if there's a message from the parent process
                message = conn.recv()
                if message == "stop":
                    break
                elif message == "start":
                    self.process_started = True
