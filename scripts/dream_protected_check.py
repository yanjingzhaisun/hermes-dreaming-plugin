#!/usr/bin/env python3
"""PORTED: paths parameterized, reads HERMES_HOME.
Verify protected (D) blocks in MEMORY.md / USER.md against rulings-table SHA-256."""
import hashlib, json, os
from pathlib import Path

# Initialize this registry from the target deployment's reviewed protected blocks.
# Empty by design: a portable package must never inherit another instance's bytes.
EXPECTED = {"MEMORY.md": {}, "USER.md": {}}


def check(home, expected):
    out = {}
    for fname, blocks in expected.items():
        path = Path(home) / 'memories' / fname
        # Preserve CRLF: universal-newline conversion can hide changed bytes.
        with path.open(encoding='utf-8', newline='') as source:
            entries = [entry.strip('\n') for entry in source.read().split('\n§\n')]
        report = []
        previous = -1
        # Registry insertion order is the required protected-block order.
        for rid, (exp, label) in blocks.items():
            matches = [(index, entry) for index, entry in enumerate(entries) if entry.startswith(label)]
            item = {'rule': rid, 'label': label}
            if not matches:
                item['status'] = 'MISSING'
            elif len(matches) != 1:
                item['status'] = 'AMBIGUOUS'
            else:
                index, entry = matches[0]
                actual = hashlib.sha256(entry.encode('utf-8')).hexdigest()
                item.update(hash=actual, expected=exp)
                item['status'] = ('HASH_MISMATCH' if actual != exp else
                                  'ORDER_MISMATCH' if index <= previous else 'OK')
                previous = max(previous, index)
            report.append(item)
        out[fname] = report
    return out


def main():
    home = Path(os.path.expanduser(os.environ.get('HERMES_HOME', '~/.hermes')))
    out = check(home, EXPECTED)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return int(any(item['status'] != 'OK' for items in out.values() for item in items))


if __name__ == '__main__':
    raise SystemExit(main())
