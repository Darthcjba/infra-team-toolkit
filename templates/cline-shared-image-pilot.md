Use the installed infra-team-toolkit to make one scoped offline change in this checkout.

For the persistent e2e-check service, change the shared backend image to docker.io/onehq/agencieshq:toolkit-pilot. This is a synthetic validation pin, not a deployable image. The API, GoodJob, Sidekiq, preparation Job, seed Job and seed readiness init must receive it. Leave the renderable PR example and unrelated component images unchanged.

Read AGENTS.md, the installed rules and cjba-k8s-jsonnet skill explicitly. Before editing, identify the canonical input, the application-pinned OneHQ revision versus the skill snapshot, the relevant derivation stages and exact offline checks. Preserve the current layout and implemented interfaces. Do not invent a constructor or capability API.

Make only the canonical image-input edit. Render the affected target and unchanged PR example without exposing Secret payloads or credential values. Verify shared consumers, Service selectors, unchanged stable identities/policy and intentionally changed Job names/dependency gates. Run the existing offline validation and summarize actual results, commands and limitations.

Do not deploy, contact the cluster/registry, run delivery scripts, push/commit, change execution inputs, upgrade dependencies or fix unrelated issues. Do not print raw manifests or literal credentials. Finish with the source diff and concise evidence. Use this single agent without delegating to other agents.
