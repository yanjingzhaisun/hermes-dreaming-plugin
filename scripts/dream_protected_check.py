#!/usr/bin/env python3
"""PORTED: paths parameterized, reads HERMES_HOME.
Verify protected (D) blocks in MEMORY.md / USER.md against rulings-table SHA-256."""
import hashlib, json, os
from pathlib import Path

# Initialize this registry from the target deployment's reviewed protected blocks.
# Empty by design: a portable package must never inherit another instance's bytes.
EXPECTED = {"MEMORY.md": {}, "USER.md": {}}


out = {}
for fname, blocks in EXPECTED.items():
    path = Path(os.path.expanduser(os.environ.get('HERMES_HOME', '~/.hermes'))) / 'memories' / fname
    text = open(path, encoding="utf-8").read()
    entries = [e.strip("\n") for e in text.split("\n§\n")]
    report = []
    for rid, (exp, label) in blocks.items():
        found = None
        for e in entries:
            if e.startswith(label[:12]):
                found = e
                break
        if found is None:
            report.append({"rule": rid, "status": "MISSING", "label": label})
        else:
            h = hashlib.sha256(found.encode("utf-8")).hexdigest()
            report.append({"rule": rid, "status": "OK" if h == exp else "HASH_MISMATCH",
                           "label": label, "hash": h, "expected": exp})
    out[fname] = report
print(json.dumps(out, ensure_ascii=False, indent=1))
