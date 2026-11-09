# Skills

`cjba-k8s-jsonnet/` combines the owner-supplied constructor guidance with the toolkit's application workflow and compatibility guidance. Its maintained entry point and API/pattern summaries now distinguish consumer-pinned interfaces from bundled examples. No personal ChatGPT skill was installed or modified.

`references/library-source.md` and `references/constructor-guide-reference.txt` remain unchanged from the supplied archive. The archive identifies source snapshot `cb49c83a43cb04e05da5e820c6fe56faed32bf73`; this update does not independently verify that commit against upstream. Consumer locked source takes precedence under rules/10-source-authority.md. The constructor guide may contain signatures from a different revision; inspect implementation before use.

For application work, the skill reads the installed standard at `docs/infra-team-toolkit/standards/app-infrastructure.md` from the consumer root, or the standard in an available toolkit checkout. Its workflow reference also summarizes the responsibilities for standalone use without an installed toolkit. Existing app layouts remain supported. The installer packages both new references automatically; Cline must still enable/load the skill, and other agents must read it explicitly as appropriate.

Future pipeline, GitOps and diagnostic skills should be added when their source contracts and validation examples are available. Never treat a planned skill as installed functionality.
