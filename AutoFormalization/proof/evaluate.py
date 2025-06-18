import os
import argparse

from tqdm import tqdm
from subprocess import Popen, PIPE, SubprocessError, TimeoutExpired
from AutoFormalization.utils import ROOT_DIR, remove_error_source, kill_process_group


def check(lean_file: str, timeout: int = 5) -> bool:
    """
    Return whether the proof contained in ``lean_file`` is valid.
    """
    command = ["lake", "env", "lean", "--run", lean_file]
    process: Popen[str] | None = None
    timeout_flag: bool = False
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
            try:
                stdout, stderr = map(
                    lambda x: remove_error_source(x.strip()),
                    process.communicate(timeout=timeout),
                )
            except TimeoutExpired:
                timeout_flag = True
                print(f"⚠️  Failed to check proof within {timeout} seconds.")

                # need to manually kill process and wait
                kill_process_group(process.pid)
                stdout, stderr = process.communicate()

            # if a timeout occurred, fail regardless of the output on stdout and stderr
            if not timeout_flag and "error" not in stdout and "error" not in stderr:
                return True

            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            return False

    except (SubprocessError, OSError) as e:
        print(f"⚠️  Lean failed to check proof: {e}")
        return False
    finally:
        if process and process.pid and not timeout_flag:
            kill_process_group(process.pid)

            # allow up to 2 s to consume pipes and reap process
            try:
                process.communicate(timeout=2)
            except (ValueError, TimeoutExpired):
                # if ValueError: communicate() was already called, no problem
                # if TimeoutExpired: give up to avoid hanging the program
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["Book", "UniGeo"],
        required=True,
        help="Testing dataset",
    )
    parser.add_argument(
        "--category",
        type=str,
        nargs="+",
        choices=[
            "",
            "Parallel",
            "Triangle",
            "Quadrilateral",
            "Congruent",
            "Similarity",
        ],
        required=True,
        help="Testing category",
    )
    parser.add_argument(
        "--reasoning",
        type=str,
        choices=["text-only", "multi-modal"],
        required=True,
        help="Reasoning Type",
    )
    parser.add_argument(
        "--num_examples", type=int, default=0, help="Number of examples"
    )
    args = parser.parse_args()

    tot = 0
    cnt = 0

    for c in args.category:
        print("Category: ", c)
        result_dir = str(
            os.path.join(
                ROOT_DIR,
                "result",
                "proof",
                args.dataset,
                args.reasoning,
                str(args.num_examples) + "shot",
                c,
            )
        )

        if args.dataset == "UniGeo":
            testing_idx = range(1, 21)
        else:
            testing_idx = [i for i in range(1, 49) if i not in {2, 6, 12, 32, 42}]

        for i in tqdm(testing_idx):
            result_file = os.path.join(result_dir, str(i) + ".lean")

            if os.path.isfile(result_file):
                tot += 1
                if check(result_file):
                    cnt += 1
            else:
                tqdm.write(
                    f"Skipping {i}: {result_file} doesn't exist or is not a file."
                )

    print(f"cnt: {cnt}, tot: {tot}, acc: {(cnt / tot) * 100 if tot != 0 else 0:.2f}%")


if __name__ == "__main__":
    main()
