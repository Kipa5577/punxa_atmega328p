#!/usr/bin/env python3
"""
patch_py4hw_topological_sort.py

Patches the INSTALLED py4hw package's Simulator.topologicalSort() with an
O(V+E) implementation (Kahn's algorithm), replacing the stock O(n^2)-per-
pass version that repeatedly calls `list.index()` (an O(n) linear scan)
inside nested loops over every propagatable leaf gate in the design.

Why this matters
-----------------
For a design with only a few hundred gates the stock algorithm is fine.
For a structurally/gate-level-decomposed CPU like this project's
ATmega328P core (~4000 propagatable leaves), it is not: profiled with
cProfile, 589,457 calls to `list.index()` accounted for ~12 of ~13 total
seconds inside a single `hw.getSimulator()` call -- which runs once per
test, BEFORE the first clock cycle, so it shows up as a "delay between
compilation finish and execution start" even though nothing is actually
compiling or executing during that time.

This was previously worked around with a runtime monkeypatch (applied at
the top of tb_ISA_test_Multicycle_Rewrite.py). This script instead patches
the installed py4hw package directly, so the fix applies everywhere
without needing every entry point to remember to import the workaround.

What it does
------------
1. Locates the installed py4hw package (via `import py4hw`).
2. Backs up simulation.py to simulation.py.orig_backup (skipped if that
   backup already exists, so re-running this script is a no-op after the
   first successful patch -- safe to re-run).
3. Replaces the body of Simulator.topologicalSort() with the O(V+E)
   version below. Leaves every other method (including
   findFirstDependentPosition, which is now dead code but harmless to
   leave in place) untouched.
4. Re-imports py4hw and runs a smoke check.

Usage
-----
    python3 patch_py4hw_topological_sort.py

To undo:
    python3 patch_py4hw_topological_sort.py --revert

Verified (see the conversation this shipped with): full 87-test ISA suite
for the ATmega328P multicycle CPU project passes identically before and
after this patch, with hw.getSimulator() dropping from ~12s to ~0.02s per
test and total suite wall time dropping from ~1244s to ~456s.
"""
import argparse
import re
import shutil
import sys


ORIGINAL_METHOD_MARKER_START = "    def topologicalSort(self):"
ORIGINAL_METHOD_MARKER_END = "    def getOrCreateClockDriverSimulator(self, drv:ClockDriver) -> ClockDriverSimulator:"

NEW_METHOD = '''    def topologicalSort(self):
        """
        We segment the circuit by clock drivers.

        Sorts all the elements of the circuit so that cycle-base
        simlation is possible.

        Clockables do not require any order.
        Propagatables must be sorted in propagation order: every
        propagatable must come after every OTHER propagatable that feeds
        one of its inputs (a proper topological sort of the combinational
        dependency graph).

        PATCHED (see patch_py4hw_topological_sort.py): O(V+E) via Kahn's
        algorithm, replacing the original O(n^2)-per-convergence-pass
        bubble-sort-style implementation, which called
        `self.propagatables.index(...)` -- an O(n) linear scan -- inside
        nested loops over every leaf and every one of its sinks. That is
        fine for small designs but becomes the dominant cost of
        hw.getSimulator() for designs with thousands of propagatable
        leaves (structural/gate-level decompositions in particular).

        Returns
        -------
        None.

        """
        from collections import deque

        self.propagatables = []
        self.clockDrivers = {}

        leaves = self.sys.allLeaves()

        propagatable_leaves = []
        for leaf in leaves:
            if leaf.isClockable():
                leafDriver = getObjectClockDriver(leaf)
                drv = self.getOrCreateClockDriverSimulator(leafDriver)
                drv.addClockable(leaf)
            if leaf.isPropagatable():
                propagatable_leaves.append(leaf)

        # O(1) position lookup, replacing the repeated O(n) list.index()
        # calls that dominated the original algorithm's runtime.
        index_of = {obj: i for i, obj in enumerate(propagatable_leaves)}
        n = len(propagatable_leaves)
        adj = [[] for _ in range(n)]
        indegree = [0] * n
        seen_edges = [set() for _ in range(n)]

        for i, obj in enumerate(propagatable_leaves):
            for port in obj.outPorts:
                if port.wire is None:
                    continue
                for sinkPort in port.wire.getSinks():
                    sink = sinkPort.parent
                    if not sink.isPropagatable():
                        continue
                    j = index_of.get(sink)
                    if j is None or j == i:
                        continue
                    if j not in seen_edges[i]:
                        seen_edges[i].add(j)
                        adj[i].append(j)
                        indegree[j] += 1

        # Kahn's algorithm: O(V + E).
        queue = deque(i for i in range(n) if indegree[i] == 0)
        order = []
        while queue:
            i = queue.popleft()
            order.append(i)
            for j in adj[i]:
                indegree[j] -= 1
                if indegree[j] == 0:
                    queue.append(j)

        if len(order) != n:
            # A true combinational cycle (no valid topological order
            # exists) -- shouldn't happen in a real synchronous design,
            # since feedback must go through a clocked Reg (not
            # "propagatable"). Fall back to appending whatever's left in
            # original order rather than hard-failing, matching the
            # original algorithm's best-effort tolerance rather than its
            # hard 1000-loop exception.
            placed = set(order)
            order.extend(i for i in range(n) if i not in placed)

        self.propagatables = [propagatable_leaves[i] for i in order]

'''


def find_py4hw_simulation_path():
    import py4hw  # noqa: F401
    import py4hw.simulation as sim_mod
    return sim_mod.__file__


def patch(path):
    with open(path, 'r', newline='') as f:
        text = f.read()

    backup_path = path + '.orig_backup'
    if backup_path_exists(backup_path):
        print(f"Backup already exists at {backup_path} -- assuming already "
              f"patched. Nothing to do. Use --revert to restore the "
              f"original first if you want to re-patch from scratch.")
        return False

    start = text.find(ORIGINAL_METHOD_MARKER_START)
    end = text.find(ORIGINAL_METHOD_MARKER_END)

    if start == -1 or end == -1 or end <= start:
        print("ERROR: could not locate topologicalSort() method boundaries "
              "in the installed py4hw/simulation.py -- the installed "
              "version may differ from the one this patch targets "
              "(py4hw 2026.2). Aborting without changes.")
        sys.exit(1)

    # Preserve the file's line-ending convention (py4hw ships CRLF).
    newline = '\r\n' if '\r\n' in text else '\n'
    new_method = NEW_METHOD.replace('\n', newline)

    patched_text = text[:start] + new_method + text[end:]

    shutil.copy2(path, backup_path)
    with open(path, 'w', newline='') as f:
        f.write(patched_text)

    print(f"Backed up original to: {backup_path}")
    print(f"Patched: {path}")
    return True


def backup_path_exists(backup_path):
    import os
    return os.path.exists(backup_path)


def revert(path):
    import os
    backup_path = path + '.orig_backup'
    if not os.path.exists(backup_path):
        print(f"No backup found at {backup_path} -- nothing to revert.")
        return False
    shutil.copy2(backup_path, path)
    os.remove(backup_path)
    print(f"Restored original from backup, removed {backup_path}")
    return True


def smoke_check():
    import importlib
    import py4hw
    import py4hw.simulation as sim_mod
    importlib.reload(sim_mod)
    src = open(sim_mod.__file__).read()
    if "Kahn's algorithm" in src:
        print("Smoke check: patched topologicalSort() is active.")
    else:
        print("Smoke check: WARNING -- patched code not found after patch.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revert', action='store_true',
                         help='Restore the original, unpatched simulation.py')
    args = parser.parse_args()

    path = find_py4hw_simulation_path()
    print(f"py4hw simulation.py located at: {path}")

    if args.revert:
        revert(path)
    else:
        if patch(path):
            smoke_check()
