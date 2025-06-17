import os
import signal

from E3.utils import ROOT_DIR, format_test_file, remove_error_source
from subprocess import Popen, PIPE


class Validator:
    def __init__(self, tmp_path=os.path.join(ROOT_DIR, "tmp", "validate")):
        self.tmp_path = tmp_path
        os.makedirs(self.tmp_path, exist_ok=True)

    def validate(self, expression, instanceName):
        tmpFile = os.path.join(self.tmp_path, instanceName + ".lean")
        os.makedirs(os.path.dirname(tmpFile), exist_ok=True)

        leanFile = format_test_file(expression)
        with open(tmpFile, "w") as file:
            file.write(leanFile)

        command = ["lake", "env", "lean", "--run", tmpFile]
        process = Popen(
            command, stdin=PIPE, stdout=PIPE, cwd=ROOT_DIR, preexec_fn=os.setsid
        )
        try:
            stdout, _ = process.communicate()
            if stdout == b"":
                return None
            else:
                return remove_error_source(stdout.decode())
        except:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return "Unexpected error"
