# Scripts

Requires Python 3.9+ and Git. No third-party Python packages.

- `python3 scripts/check.py`: check the toolkit's required content and skill metadata.
- `python3 scripts/install.py /path/to/app`: copy rules, skills and standards into a Git consumer and write a checksum manifest. Requires a clean, committed toolkit checkout. Refuses differing destination files and symlink destinations before writing.
- `python3 scripts/install.py /path/to/app --check`: compare an installed consumer against this toolkit checkout. Does not write.
- `python3 scripts/worked-shared-image.py /path/to/agencieshq-e2e-infra`: run the Step 4 shared-image example against the clean documented reference revision using in-memory inputs; print a report without raw manifests. Requires Tanka and the app's locked dependencies. Add `--validate-app` to run the full offline app suite in a disposable local clone with copied dependencies (Python 3.10+ and Ruby required). See [the walkthrough](../standards/examples/shared-backend-image.md) for the exact revision, synthetic inputs and expected results. This script is reference-specific and is not installed into consumers.
- `python3 scripts/map-kubernetes.py --app /path/to/app --environment environments/example --output generated/kubernetes/example`: render and map resource identities, allowlisted attributes and supported references to HTML/JSON/Mermaid. Or use `--input rendered.json` for existing JSON. Add `--infer-env-links` for explicitly inferred endpoint/Job links. See [coverage and controls](../standards/kubernetes-map.md). Uses the standard library and a bundled HTML template; scripts/templates are not installed into consumers.

Installation does not edit AGENTS.md, install binaries, fetch dependencies, authenticate Cline or modify GitHub permissions. Templates are copied manually after review.

For an upgrade, use a clean consumer branch, remove only files listed in its previous `.infra-team-toolkit.json` after reviewing local changes, then install the new reviewed revision and inspect the diff. The installer deliberately provides no force-overwrite mode. Check mode verifies this checkout's expected files; review old manifest entries for files retired by a newer release.
