import os
import re
import signal


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def format_test_file(test):
    return f"""import SystemE
import UniGeo.Relations
import E3
import Qq

set_option autoImplicit false
set_option linter.unusedVariables false

open Qq Lean

def testE : Expr := q({test})

def main : IO Unit := WfChecker testE
"""


def format_lean_checker_file(ground, test):
    return f"""import SystemE
import UniGeo.Relations
import E3
import Qq

set_option autoImplicit false
set_option linter.unusedVariables false

open Qq Lean

def ground : Prop := {ground}
def test : Prop := {test}
def groundE : Expr := q({ground})
def testE : Expr := q({test})

def main (args : List String) : IO Unit := do 
    let xs ← parseArgs args
    runE3fromIO groundE testE xs
"""


def remove_error_source(message: str) -> str:
    """
    Strip the leading error source from a Lean error message.

    Example:
    >>> remove_error_source(
        "/home/johndoe/.../LeanEuclid/result/proof/Book/text-only/0shot/2.lean:6:35: error: ..."
    )
    error: ...
    """
    return re.sub(r"/[^:]+:\d+:\d+: ", "", message)


def kill_process_group(pgid: int) -> None:
    """
    Kill all processes in the process group using ``SIGKILL``.
    Useful for killing z3 and cvc5 solvers spawned by a checker.

    :param pgid: ID of the process group to kill
    """
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        # Process group already exited
        pass
    except PermissionError:
        print("⚠️  Insufficient permission to kill process group", pgid)
