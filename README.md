# Verifying LinearSearch with the repair loop

`LinearSearch` verifies with Dafny 4.11.0 in one round of the live repair loop. Its specification is still weaker than intended: two wrong bodies also verify. A stronger specification rejects both.

## The method and its specification

`LinearSearch` should return the index of the **first** occurrence of `key` in an `int` array, or `-1` if `key` does not occur. This is Python's `list.index`, returning `-1` instead of raising.

```dafny
method LinearSearch(a: array<int>, key: int) returns (i: int)
  ensures 0 <= i ==> i < a.Length && a[i] == key
  ensures i < 0 ==> forall j :: 0 <= j < a.Length ==> a[j] != key
```

The two `ensures` clauses follow the "found" and "absent" clauses of the lecture's `BinarySearch` spec, without its sortedness requirement.

## Results

**Live run.** `--model openrouter/auto` produced a verified body in round 1 (`2 verified, 0 errors`). Log: `run_log_live.txt`.

**Mock replay.** Because the live run passed at once, the feedback step never fired. `mock_attempts/` holds three increasingly complete bodies that show it working. Log: `run_log.txt`.

| Round | What the body added | Verifier output |
| --- | --- | --- |
| 1 | Loop that returns at the first match, else -1; no invariants | `a postcondition could not be proved on this return path` (the "absent" clause) |
| 2 | `invariant forall j :: 0 <= j < i ==> a[j] != key` | `index out of range` inside that invariant |
| 3 | `invariant 0 <= i <= a.Length` | `2 verified, 0 errors` |

**Bodies against both specs** (checked with `check.sh`):

| Body | `LinearSearch.spec.dfy` | `LinearSearch.strong.spec.dfy` |
| --- | --- | --- |
| Correct (`mock_attempts/attempt3.dfy`) | Verified | Verified |
| `wrong/LastOccurrence.body.dfy` | Verified (wrong) | Rejected: first-occurrence clause |
| `wrong/MinusSeven.body.dfy` | Verified (wrong) | Rejected: `-1 <= i` |
| `wrong/Quadratic.body.dfy` (O(n²)) | Verified | Verified: cost is in neither spec |

## Critique of the specification

The spec promises "some index holding key, or some negative number if key is absent", not the intended "the first occurrence, or -1". It never says which index to return when key occurs more than once, and never says which negative value means "absent". `LastOccurrence` returns the last match (on `[3, 7, 7]` with key 7 it returns 2, not 1), and `MinusSeven` returns -7 when key is missing; both verify. The lecture's `BinarySearch` spec has the same gap in its absent case: it would also accept Java's convention of returning -(insertion point) - 1. The spec is also silent on cost, so an O(n²) body verifies too. It does not need to say the array is unchanged: with no `modifies` clause, Dafny rejects any write to `a`.

The stronger spec pins down both gaps:

```dafny
method LinearSearch(a: array<int>, key: int) returns (i: int)
  ensures -1 <= i < a.Length
  ensures 0 <= i ==> a[i] == key && forall j :: 0 <= j < i ==> a[j] != key
  ensures i == -1 ==> forall j :: 0 <= j < a.Length ==> a[j] != key
```

## Files

| Path | Contents |
| --- | --- |
| `LinearSearch.spec.dfy` | The submitted spec (signature and `ensures` only) |
| `LinearSearch.strong.spec.dfy` | The strengthened spec |
| `mock_attempts/attempt1-3.dfy` | Bodies replayed by `repair_loop.py --mock` |
| `wrong/*.body.dfy` | Bodies that verify against the submitted spec but are wrong or wasteful |
| `run_log.txt`, `run_log_live.txt` | Output of the mock replay and of the live run |
| `check.sh` | Verifies one body against one spec, as `repair_loop.py` does |
| `repair_loop.py` | From the course's `lecture-code/part3_verifiers/` (unchanged) |

## How to run

Requirements: Dafny 4.11.0 on `PATH` (the Ubuntu `apt` package is Dafny 2.x and does not understand `dafny verify`), Python 3, and [uv](https://docs.astral.sh/uv/) for the live run.

```bash
# Replay the three-round loop (standard library only)
python3 repair_loop.py --mock --spec LinearSearch.spec.dfy

# Check one body against one spec
bash check.sh LinearSearch.spec.dfy wrong/LastOccurrence.body.dfy

# Live run: put OPENROUTER_API_KEY=... in .env (never committed)
uv run --no-project --env-file .env --with openai python -u repair_loop.py \
  --spec LinearSearch.spec.dfy --model openrouter/auto 2>&1 | tee run_log_live.txt
```

