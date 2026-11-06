# Scripts

Requires Python 3.9+ and Git. No third-party Python packages.

- `python3 scripts/check.py`: check the toolkit's required content and skill metadata.
- `python3 scripts/install.py /path/to/app`: copy rules, skills and standards into a Git consumer and write a checksum manifest. Requires a clean, committed toolkit checkout. Refuses differing destination files and symlink destinations before writing.
- `python3 scripts/install.py /path/to/app --check`: compare an installed consumer against this toolkit checkout. Does not write.

Installation does not edit AGENTS.md, install binaries, fetch dependencies, authenticate Cline or modify GitHub permissions. Templates are copied manually after review.

For an upgrade, use a clean consumer branch, remove only files listed in its previous `.infra-team-toolkit.json` after reviewing local changes, then install the new reviewed revision and inspect the diff. The installer deliberately provides no force-overwrite mode. Check mode verifies this checkout's expected files; review old manifest entries for files retired by a newer release.
