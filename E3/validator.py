import os

from E3.utils import ROOT_DIR, format_test_file, remove_error_source, kill_process_group
from subprocess import Popen, PIPE, SubprocessError, TimeoutExpired


class Validator:
    def __init__(self, tmp_path=os.path.join(ROOT_DIR, "tmp", "validate")):
        self.tmp_path = tmp_path
        os.makedirs(self.tmp_path, exist_ok=True)

    def validate(self, expression: str, instance_name: str) -> str | None:
        """
        Return ``None`` if validation succeeds. Otherwise, return a cleaned version of the error or warning that can be passed back to the model.
        """
        tmp_file = os.path.join(self.tmp_path, instance_name + ".lean")
        os.makedirs(os.path.dirname(tmp_file), exist_ok=True)

        lean_file = format_test_file(expression)
        with open(tmp_file, "w") as file:
            file.write(lean_file)

        command = ["lake", "env", "lean", "--run", tmp_file]
        try:
            with Popen(
                command,
                stdout=PIPE,
                stderr=PIPE,
                cwd=ROOT_DIR,
                start_new_session=True,
                text=True,
                encoding="utf-8",
            ) as process:
                stdout, stderr = map(
                    lambda x: remove_error_source(x.strip()),
                    process.communicate(),
                )

                # validator gave an error or warning
                if stdout:
                    return stdout
                if stderr:
                    return stderr

                # validator exited normally
                return None

        except (SubprocessError, OSError) as e:
            print(f"⚠️  Failed to execute validator: {e}")
            return "Unexpected error"

        finally:
            if process and process.pid:
                kill_process_group(process.pid)

                # allow up to 2 s to consume pipes and reap process
                try:
                    process.communicate(timeout=2)
                except (ValueError, TimeoutExpired):
                    # if ValueError: communicate() was already called, no problem
                    # if TimeoutExpired: give up to avoid hanging the program
                    pass
