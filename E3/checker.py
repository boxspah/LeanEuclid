import os
import json

from E3.utils import (
    ROOT_DIR,
    format_lean_checker_file,
    remove_error_source,
    kill_process_group,
)
from subprocess import Popen, PIPE, SubprocessError, TimeoutExpired


class Checker:
    def __init__(
        self,
        n_perms=3,
        bin_time=15,
        approx_time=5,
        mode="skipApprox",
        tmp_path=os.path.join(ROOT_DIR, "tmp", "check"),
        result_path=os.path.join(ROOT_DIR, "results"),
    ):
        self.tmp_path = tmp_path
        os.makedirs(self.tmp_path, exist_ok=True)
        self.result_path = result_path
        os.makedirs(self.result_path, exist_ok=True)

        self.n_permutations = n_perms
        self.equiv_solver_time = bin_time
        self.approx_solver_time = approx_time
        self.mode = mode

    def check(self, ground: str, test: str, instance_name: str) -> bool:
        """
        Check the logical equivalence of ``ground`` and ``test`` using E3, and write the
        result to a file with the same name as the ``instance_name``.

        :returns: ``True`` iff ``ground`` is equivalent to ``test``
        """
        tmp_file = os.path.join(self.tmp_path, instance_name + ".lean")
        with open(tmp_file, "w") as file:
            lean_file = format_lean_checker_file(ground, test)
            file.write(lean_file)
        output_json_file = os.path.join(self.result_path, instance_name + ".json")

        command = [
            "lake",
            "env",
            "lean",
            "--run",
            tmp_file,
            instance_name,
            self.mode,
            str(self.n_permutations),
            str(self.equiv_solver_time),
            str(self.approx_solver_time),
            "true",
            output_json_file,
        ]

        process: Popen[str] | None = None
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
                    lambda x: remove_error_source(x.strip()), process.communicate()
                )

                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr)

                if "error" in stdout or stderr:
                    return False

                try:
                    with open(output_json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return data[instance_name]["binary_check"] == "equiv"
                except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                    print(f"⚠️  Failed to parse output file: {e}")
                    return False
        except (SubprocessError, OSError) as e:
            print(f"⚠️  Failed to execute checker: {e}")
            return False
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
