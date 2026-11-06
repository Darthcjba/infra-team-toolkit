# Governance

## Current ownership

Darthcjba is the sole accountable owner and maintainer. No team delegation is defined yet.

| Area | Responsible and accountable |
| --- | --- |
| Repository access, settings and integrations | @Darthcjba |
| Architecture standards and exceptions | @Darthcjba |
| Rules, skills and source compatibility | @Darthcjba |
| Install scripts and validation | @Darthcjba |
| Review, merge, release and rollback decisions | @Darthcjba |
| Application adoption and onboarding | @Darthcjba |

## Decisions and releases

Use branches and review the complete diff before merging. During the solo phase the owner may review and merge their own change; do not require a second person's approval. Record behavior changes in CHANGELOG.md. Tag reviewed, tested releases and record exact toolkit revisions in consumers.

## GitHub access

CODEOWNERS records review ownership; it does not grant, revoke or enforce access. Repository settings are the authority for collaborators, installations, deploy keys and rulesets. Desired initial state: only Darthcjba has human write/admin access. Audit existing access before changing it. Do not add collaborators until the owner requests it. Repository visibility is a separate decision; do not change it as part of this scaffold.

These files do not configure GitHub permissions or branch protection. Avoid an approval rule that prevents the only maintainer from merging. When team members join, explicitly assign scopes and update both GitHub access and CODEOWNERS.
