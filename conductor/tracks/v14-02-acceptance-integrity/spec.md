# Acceptance integrity: source register, artifact manifests and gate-green evidence

Design authority: [../../v14-design.md](../../v14-design.md).
Implementation scope: make the acceptance chain self-consistent — the source register
pins the retrieval tool's own bytes, and the artifact manifests pin every calculation
input, so any later edit silently invalidates a seal. This track records the ordering
rule, fixes the current mismatches, and produces a genuinely green full-profile run plus
hosted evidence. It changes no model number and no output bytes.
