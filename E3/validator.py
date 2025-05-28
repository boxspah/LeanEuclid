import os
import re
import signal

from E3.utils import *
from subprocess import Popen, PIPE, SubprocessError


class Validator:
    def __init__(self, tmp_path=os.path.join(ROOT_DIR, "tmp", "validate")):
        self.tmp_path = tmp_path
        os.makedirs(self.tmp_path, exist_ok=True)

    def validate(self, expression, instance_name):
        tmp_file = os.path.join(self.tmp_path, instance_name + ".lean")
        os.makedirs(os.path.dirname(tmp_file), exist_ok=True)

        lean_file = format_test_file(expression)
        with open(tmp_file, "w") as file:
            file.write(lean_file)

        process = None
        command = ["lake", "env", "lean", "--run", tmp_file]
        try:
            process = Popen(
                command, stdin=PIPE, stdout=PIPE, cwd=ROOT_DIR, preexec_fn=os.setsid
            )
            stdout, _ = process.communicate()
            if stdout == b"":
                return None
            else:
                error = stdout.decode()
                error = re.sub(r"/[^:]+:\d+:\d+: ", "", error)
                return error
        except (SubprocessError, OSError) as e:
            print(f"Unexpected error: {e}")
            if process:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return "Unexpected error"
