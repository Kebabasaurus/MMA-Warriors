# Source delivery snapshot

`delivery-manifest.json` is the current machine-readable proposal for a reviewable
MMA Warriors source delivery. It records every included path, its role, canonical
content size and SHA-256 hash. Text is identified with LF line endings so the same
commit validates after either LF or CRLF checkout; binary assets use raw bytes.
It does not stage, commit, release or build anything.

Refresh the manifest after an authorized source/documentation change, then create
and validate a new copy outside the repository:

```powershell
py -3.13 tools/update_delivery_manifest.py
py -3.13 tools/validate_delivery_manifest.py --copy-to "D:\CodexFILES\MMA-Warriors-delivery-20260918-1"
```

The destination must not already exist. Validation rechecks every copied hash,
the aggregate content identity, local Python imports, every registered runner
script and existing registered fixture, the authoritative packaging inputs and
Python syntax from the copied files. This prevents imports from silently resolving
back to the working checkout.

The manifest intentionally excludes active `Saves`, `Logs` and the local
`active_universe.txt` selection marker, plus credentials/tool metadata, caches
and packaging outputs. It also avoids copying all retained
analysis history: named source-bound JSON fixtures and the current ranked portrait
review fixtures are included; generated and historical outputs remain classified
as evidence in the repository. The analysis navigation index and authoritative
feature ledger are explicit documentation dependencies even though blanket
analysis history is excluded. The manifest's `unresolved_ownership_decisions`
array must be empty before calling the snapshot dependency-complete.
