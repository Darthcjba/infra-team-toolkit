# Toolkit maintenance

Read README.md and GOVERNANCE.md before changes. @Darthcjba owns all areas.
This repository distributes instructions and documentation; it does not deploy infrastructure.
Preserve `skills/cjba-k8s-jsonnet/` as the supplied upstream snapshot unless a skill change is explicitly scoped. Consumer-specific source precedence is defined in rules/10-source-authority.md.
Run `python3 scripts/check.py`, `python3 -m unittest discover -s tests -v`, and `git diff --check` for script changes.
Do not invent implemented application APIs from proposed architecture documents. Do not silently replace consumer files or modify GitHub access settings.
