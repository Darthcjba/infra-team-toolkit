# Contributing

Current maintainer: @Darthcjba. This workflow also applies to owner-authored changes.

1. Create a focused branch and identify the affected rules, skills, standards or scripts.
2. Preserve consumer compatibility or document the migration and rollback.
3. Run `python3 scripts/check.py` and `python3 -m unittest discover -s tests -v`.
4. For constructor guidance changes, inspect the consumer's pinned library source and validate a representative application when available. Toolkit checks do not render Kubernetes resources.
5. Review `git diff --check` and the complete diff. Record validation limits in the PR.
6. Update CHANGELOG.md. The owner decides when to merge and tag a release.

Do not commit credentials, kubeconfigs, resolved secret manifests or local machine configuration. Changes to generated consumer copies belong upstream; install a reviewed toolkit revision to adopt them.
