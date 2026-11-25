"""Page replacement algorithms: FIFO, LRU, Optimal.

Optimised core: every reference is processed in O(frames) time.
  * FIFO    -> remembers WHEN each page was loaded
  * LRU     -> remembers WHEN each page was last used
  * Optimal -> pre-computes WHEN each page will be used next (one backward pass)

Each function returns a dict:
  steps  : one entry per reference (page, frames, hit, victim, slot, reason, cumulative counts)
  hits / faults / total
Console test:  python algorithms.py
"""
INF = float("inf")


def _next_occurrences(refs):
    """nxt[i] = index of the next time refs[i] appears after position i (INF if never)."""
    nxt, seen = [INF] * len(refs), {}
    for i in range(len(refs) - 1, -1, -1):
        nxt[i] = seen.get(refs[i], INF)
        seen[refs[i]] = i
    return nxt


def _simulate(refs, n_frames, pick_victim):
    slots = [None] * n_frames                      # the frames (None = empty)
    st = {"loaded": {}, "last": {}, "next": {}}    # per-page bookkeeping used by the rules
    nxt = _next_occurrences(refs)
    steps, hits = [], 0

    for i, page in enumerate(refs):
        victim = None
        if page in slots:                                        # HIT
            idx = slots.index(page)
            hit = True
            hits += 1
            reason = f"Page {page} is already in Frame {idx + 1} -> HIT! Nothing to replace."
        else:                                                    # PAGE FAULT
            hit = False
            if None in slots:
                idx = slots.index(None)
                reason = (f"Page {page} is not in memory -> PAGE FAULT. "
                          f"Frame {idx + 1} is free, so just load it.")
            else:
                idx, why = pick_victim(slots, i, st)
                victim = slots[idx]
                for table in st.values():
                    table.pop(victim, None)
                reason = (f"Page {page} is not in memory -> PAGE FAULT. Frames are full. "
                          f"{why} Replace it in Frame {idx + 1}.")
            slots[idx] = page
            st["loaded"][page] = i
        st["last"][page] = i
        st["next"][page] = nxt[i]

        steps.append({"page": page, "frames": slots.copy(), "hit": hit, "victim": victim,
                      "slot": idx, "reason": reason,
                      "cum_hits": hits, "cum_faults": i + 1 - hits})

    total = len(refs)
    return {"steps": steps, "hits": hits, "faults": total - hits, "total": total}


def _fifo_victim(slots, i, st):
    k = min(range(len(slots)), key=lambda k: st["loaded"][slots[k]])
    v = slots[k]
    return k, f"FIFO evicts the oldest page: {v} (loaded at step {st['loaded'][v] + 1})."


def _lru_victim(slots, i, st):
    k = min(range(len(slots)), key=lambda k: st["last"][slots[k]])
    v = slots[k]
    return k, f"LRU evicts the least recently used page: {v} (last used at step {st['last'][v] + 1})."


def _optimal_victim(slots, i, st):
    k = max(range(len(slots)), key=lambda k: st["next"][slots[k]])
    v, when = slots[k], st["next"][slots[k]]
    if when == INF:
        return k, f"Optimal evicts page {v} - it is never used again."
    return k, f"Optimal evicts page {v} - it is needed farthest in the future (step {when + 1})."


def fifo(refs, n_frames):
    return _simulate(refs, n_frames, _fifo_victim)


def lru(refs, n_frames):
    return _simulate(refs, n_frames, _lru_victim)


def optimal(refs, n_frames):
    return _simulate(refs, n_frames, _optimal_victim)


ALGORITHMS = {"FIFO": fifo, "LRU": lru, "OPTIMAL": optimal}


def run_all(refs, n_frames):
    return {name: fn(refs, n_frames) for name, fn in ALGORITHMS.items()}


if __name__ == "__main__":
    refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    for name, r in run_all(refs, 3).items():
        print(f"{name:8} hits={r['hits']:2} faults={r['faults']:2}")
