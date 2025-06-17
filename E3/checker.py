import os
import signal
import json

from E3.utils import ROOT_DIR, format_lean_checker_file
from subprocess import Popen, PIPE, SubprocessError


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

    def check(self, ground, test, instance_name):
        tmp_file = os.path.join(self.tmp_path, instance_name + ".lean")
        with open(tmp_file, "w") as file:
            lean_file = format_lean_checker_file(ground, test)
            file.write(lean_file)
        output_json_file = os.path.join(self.result_path, instance_name + ".json")
        process = None
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

        try:
            process = Popen(
                command, stdin=PIPE, stdout=PIPE, cwd=ROOT_DIR, preexec_fn=os.setsid
            )
            stdout, stderr = (
                x.decode() if x is not None else None for x in process.communicate()
            )
            with open(output_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = data[instance_name]["binary_check"]
            if result == "equiv":
                return True
            else:
                print(f"{stdout=}")
                print(f"{stderr=}")
                return False
        except (SubprocessError, OSError) as e:
            print(f"Unexpected error: {e}")
            if process:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return False
