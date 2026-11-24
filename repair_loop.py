#!/usr/bin/env python3
"""Verifier-in-the-loop repair: an LLM writes a Dafny method body, the Dafny
verifier judges it, and the verifier's error message becomes the next prompt.

The model only ever supplies the BODY. This script pastes that body under a
spec file the model cannot edit, so the model cannot weaken the specification.

Usage
  python repair_loop.py --mock                 # offline: replay 3 canned attempts
  python repair_loop.py --model openrouter/auto # live, needs OPENROUTER_API_KEY
  python repair_loop.py --spec Other.spec.dfy --model <id>

Needs the `dafny` CLI on PATH (or pass --dafny /path/to/dafny).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

SYSTEM = """You write Dafny method bodies that pass the Dafny verifier.
You are given a method signature with its requires/ensures clauses.
Reply with ONLY the method body in one ```dafny code block.
The body starts with { and ends with }.
Do not repeat the signature. Include every loop invariant and decreases
clause the verifier needs. Never use `assume` or any {:attribute}."""

# Constructs that make the verifier say yes without proving anything.
FORBIDDEN = [
    (r"\bassume\b", "`assume` statement"),
    (r"\{:", "{:attribute} (for example {:verify false} or {:axiom})"),
    (r"\bexpect\b", "`expect` statement (a runtime check, not a proof)"),
]


def extract_body(reply: str) -> str:
    """Pull the method body out of the model's reply."""
    block = re.search(r"```(?:dafny)?\s*\n(.*?)```", reply, re.DOTALL)
    body = (block.group(1) if block else reply).strip()
    if not (body.startswith("{") and body.endswith("}")):
        raise ValueError("reply is not a single { ... } method body")
    return body


def cheats(body: str) -> list:
    """Return a description of each forbidden construct found in the body."""
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", body, flags=re.DOTALL)
    return [what for pattern, what in FORBIDDEN if re.search(pattern, code)]


def verify(dafny: str, spec: str, body: str, time_limit: int):
    """Paste body under spec, run the verifier, return (ok, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "Candidate.dfy"
        path.write_text(spec.rstrip() + "\n" + body + "\n")
        proc = subprocess.run(
            [dafny, "verify", str(path),
             "--verification-time-limit", str(time_limit)],
            capture_output=True, text=True,
        )
        out = (proc.stdout + proc.stderr).replace(str(path), "Candidate.dfy")
        return proc.returncode == 0, out.strip()


def live_attempts(model: str, spec: str):
    """Generator of model replies. Send it the verifier output to continue."""
    from openai import OpenAI  # imported here so --mock needs no packages

    client = OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Write the body for:\n\n" + spec},
    ]
    while True:
        reply = client.chat.completions.create(model=model, messages=messages)
        text = reply.choices[0].message.content
        feedback = yield text
        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": feedback})


def mock_attempts():
    """Replay canned attempts so the demo runs with no network."""
    for path in sorted((HERE / "mock_attempts").glob("attempt*.dfy")):
        yield "```dafny\n" + path.read_text() + "```"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--spec", default=str(HERE / "BinarySearch.spec.dfy"))
    p.add_argument("--model", default="openrouter/auto")
    p.add_argument("--mock", action="store_true", help="replay canned attempts")
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--dafny", default="dafny")
    p.add_argument("--time-limit", type=int, default=30, help="seconds per proof")
    args = p.parse_args()

    spec = Path(args.spec).read_text()
    attempts = mock_attempts() if args.mock else live_attempts(args.model, spec)
    print("SPEC (fixed, the model cannot change it)\n" + spec)

    feedback = None
    for round_no in range(1, args.rounds + 1):
        try:
            reply = attempts.send(feedback) if feedback else next(attempts)
        except StopIteration:
            print("No more attempts available.")
            return 1

        print(f"\n===== Round {round_no}: model's body =====")
        try:
            body = extract_body(reply)
        except ValueError as err:
            print(reply)
            feedback = f"Rejected before verification: {err}. " \
                       "Reply with only the { ... } body in a dafny code block."
            print("\n" + feedback)
            continue
        print(body)

        found = cheats(body)
        if found:
            feedback = "Rejected before verification. Not allowed: " + \
                       "; ".join(found) + ". Prove it instead."
            print("\n" + feedback)
            continue

        ok, output = verify(args.dafny, spec, body, args.time_limit)
        print(f"\n----- Round {round_no}: verifier says -----\n{output}")
        if ok:
            print(f"\nVERIFIED in {round_no} round(s).")
            return 0
        feedback = "The Dafny verifier rejected that body:\n\n" + output + \
                   "\n\nFix it. Reply with the complete corrected body only."

    print(f"\nNot verified after {args.rounds} rounds.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
