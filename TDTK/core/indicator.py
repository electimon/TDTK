from progress.spinner import Spinner
from progress import SHOW_CURSOR
from multiprocessing import Process, Pipe
import time

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
        self.parent_conn, self.child_conn = Pipe()
        self._process = Process(target=self.next, args=(self.child_conn,), daemon=True)

    def start(self):
        self.run = True
        self._process.start()

    def stop(self):
        self.spinner.stop()
        self.run = False
        self.parent_conn.send("stop")  # Signal the child process to stop
        self._process.join()  # Wait for the process to finish before returning
        # Clear the stdout line

    def next(self, conn):
        while self.run:
            self.spinner.next()
            time.sleep(0.1)  # Adjust the sleep time based on your needs
            if conn.poll():  # Check if there's a message from the parent process
                message = conn.recv()
                if message == "stop":
                    break
        self.spinner.done = True
        self.spinner.next()
        conn.close()