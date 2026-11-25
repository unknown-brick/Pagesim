"""Test cases with EXPECTED (hand-verified / textbook) vs ACTUAL results.
Run in the console:  python test_cases.py      (the GUI also shows these: Tools > Run test cases)
Expected values are page-fault counts.
"""
from algorithms import run_all

BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
CASES = [
    ("TC1  Textbook reference string, 3 frames",
     [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1], 3,
     {"FIFO": 15, "LRU": 12, "OPTIMAL": 9}),
    ("TC2  Belady's string, 3 frames", BELADY, 3, {"FIFO": 9, "LRU": 10, "OPTIMAL": 7}),
    ("TC3  Belady's string, 4 frames (FIFO gets WORSE)", BELADY, 4, {"FIFO": 10, "LRU": 8, "OPTIMAL": 6}),
    ("TC4  Edge case: same page repeated", [5, 5, 5, 5, 5], 3, {"FIFO": 1, "LRU": 1, "OPTIMAL": 1}),
    ("TC5  Edge case: all pages different", [1, 2, 3, 4, 5], 2, {"FIFO": 5, "LRU": 5, "OPTIMAL": 5}),
    ("TC6  Edge case: only 1 frame", [1, 2, 1, 2, 1, 2], 1, {"FIFO": 6, "LRU": 6, "OPTIMAL": 6}),
]


def run_tests():
    out = []
    for name, refs, frames, expected in CASES:
        actual = run_all(refs, frames)
        rows = [(a, expected[a], actual[a]["faults"], expected[a] == actual[a]["faults"]) for a in expected]
        out.append({"name": name, "refs": refs, "frames": frames, "rows": rows})
    return out


if __name__ == "__main__":
    results = run_tests()
    for case in results:
        print(f"\n{case['name']}\n  refs={case['refs']} frames={case['frames']}")
        for algo, exp, act, ok in case["rows"]:
            print(f"  {algo:8} expected={exp:3} actual={act:3}  {'PASS' if ok else 'FAIL'}")
    total = sum(len(c["rows"]) for c in results)
    passed = sum(r[3] for c in results for r in c["rows"])
    print(f"\n{passed}/{total} checks passed")
