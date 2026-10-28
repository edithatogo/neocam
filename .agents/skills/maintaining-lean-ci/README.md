# Portable lean-CI skill

`SKILL.md` is the canonical instruction; `scripts/audit_evidence.py` is a dependency-free Python evidence checker. Keep this directory under a project's `.agents/skills/`, or copy it into the user-level skills directory supported by your development agent. Do not overwrite an existing skill without reviewing differences.

The Panda Vision AGENTS.md/GEMINI.md explicitly reference it. A downloaded archive does not install a skill into ChatGPT or automatically make it active in unrelated projects.

Validation: executable adversarial receipt contracts and author review. Independent fresh-agent baseline/pressure testing was unavailable and is not claimed. Full tests and baseline evidence are in the companion Panda Vision repository (`tests/test_v4_skill.py`, `verification/v4/skill_*`).

The checker rejects partial/cached acceptance, unavailable gates, empty independent scope, conflicting fingerprints, altered logs and invalid paths. A valid receipt is consistency evidence, not an authenticated statement that an untrusted author genuinely ran a tool. The caller must supply its own required-gate list and expected fingerprint.
