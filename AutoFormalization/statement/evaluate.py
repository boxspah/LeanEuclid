import os
import json
import argparse

from tqdm import tqdm
from E3.checker import Checker
from E3.utils import ROOT_DIR


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
        "--mode",
        choices=["bvars", "skipApprox", "onlyApprox", "full"],
        default="skipApprox",
        help="E3 checker mode",
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

    cnt = 0
    tot = 0

    for c in args.category:
        print("Category: ", c)
        pred_dir = str(
            os.path.join(
                ROOT_DIR,
                "result",
                "statement",
                args.dataset,
                args.reasoning,
                str(args.num_examples) + "shot",
                c,
            )
        )
        result_dir = os.path.join(
            ROOT_DIR,
            "result",
            "equivalence",
            args.dataset,
            args.reasoning,
            str(args.num_examples) + "shot",
            c,
        )
        checker = Checker(
            tmp_path=os.path.join(
                ROOT_DIR,
                "tmp",
                "check",
                args.dataset,
                args.reasoning,
                str(args.num_examples) + "-shot",
                c,
            ),
            mode=args.mode,
            result_path=result_dir,
        )

        if args.dataset == "UniGeo":
            testing_idx = range(1, 21)
        else:
            testing_idx = [i for i in range(1, 49) if i not in {2, 6, 12, 32, 42}]

        for i in tqdm(testing_idx):
            pred_file = os.path.join(pred_dir, str(i) + ".json")

            if os.path.isfile(pred_file):
                tot += 1
                with open(pred_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                pred = data["prediction"]
                formalization = data["groud_truth"]

                try:
                    if checker.check(formalization, pred, str(i)):
                        cnt += 1
                except Exception as e:
                    tqdm.write(str(e))
                    continue
            else:
                tqdm.write(f"Skipping {i}: {pred_file} doesn't exist or is not a file.")

    print(f"cnt: {cnt}, tot: {tot}, acc: {(cnt / tot) * 100 if tot != 0 else 0:.2f}%")


if __name__ == "__main__":
    main()
