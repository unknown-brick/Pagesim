"""Export helpers: CSV trace and plain-text report (handy for the project documentation)."""
import csv


def write_csv(path, refs, n, results):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Algorithm", "Step", "Reference"] + [f"Frame {k + 1}" for k in range(n)]
                   + ["Result", "Evicted page", "Hits so far", "Faults so far"])
        for name, res in results.items():
            for i, s in enumerate(res["steps"], start=1):
                w.writerow([name, i, s["page"]] + ["" if v is None else v for v in s["frames"]]
                           + ["HIT" if s["hit"] else "FAULT", "" if s["victim"] is None else s["victim"],
                              s["cum_hits"], s["cum_faults"]])


def to_text(refs, n, results):
    lines = ["PAGE REPLACEMENT SIMULATION REPORT", "=" * 34,
             f"Reference string : {' '.join(map(str, refs))}", f"Number of frames : {n}", ""]
    for name, res in results.items():
        total = res["total"]
        lines += [f"{name}", "-" * len(name),
                  f"Hits: {res['hits']}   Faults: {res['faults']}   "
                  f"Hit ratio: {res['hits'] / total * 100:.2f}%   Fault ratio: {res['faults'] / total * 100:.2f}%",
                  "Ref     : " + "".join(f"{s['page']:>3}" for s in res["steps"])]
        for k in range(n):
            cells = "".join(f"{'-' if s['frames'][k] is None else s['frames'][k]:>3}" for s in res["steps"])
            lines.append(f"Frame {k + 1} : " + cells)
        lines += ["Result  : " + "".join(f"{'H' if s['hit'] else 'F':>3}" for s in res["steps"]), ""]
    best = min(r["faults"] for r in results.values())
    lines.append("Fewest faults: " + ", ".join(n_ for n_, r in results.items() if r["faults"] == best))
    return "\n".join(lines)


def write_text(path, refs, n, results):
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_text(refs, n, results))
