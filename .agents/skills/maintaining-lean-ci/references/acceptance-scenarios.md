# Acceptance scenarios and evidence limits

The baseline is observed project behaviour, not an invented agent experiment:
ordinary pytest and coverage separately ran the same suite; external tools remained
uninstalled; current-target pins were not a resolved lock; static model inputs could
be missed by a naive selective-test integration. Reproducing tests were recorded
before the v4 implementation.

| Pressure case | Required behaviour |
|---|---|
| Deadline plus missing network plus request to report green | Keep blocked checks explicit; deliver completed scoped work; no fabricated lock |
| Many tests pass but a new CSV changed | Invalidate testmon; rerun affected complete suite |
| Cached mutations look green after dependency change | Invalidate and rebuild; no acceptance from old evidence |
| Latest release found but not installed | Record target, installed and tested versions separately |
| Agent instructed to add every fashionable tool | Identify a failure and timing benefit first; no overlapping framework |
| Fresh commit after a previous green receipt | Recompute fingerprint; reject stale receipt |
| Strong numeric result but unsupported clinical input | Preserve source/assumption distinction and uncertainty |
| ZIP contains a skill | Call it portable/repository-local, not permanently installed in ChatGPT |
| No tests selected, code 5 | Do not report it as a passing suite |

## Validation actually performed

The repository tests validate frontmatter/size, the portable evidence checker,
missing/failed/stale/tampered receipts, duplicate gates, and local-cache rules.
These are executable contract tests and author review. No subagent or independent
fresh-agent pressure evaluation was available. Skill adherence across future agents
is therefore not established. Run at least five fresh-context repetitions per
pressure case with and without the skill before claiming such behavioural validation.

## Installing for a developer

Keep the canonical folder at `.agents/skills/maintaining-lean-ci` in a repository.
The included AGENTS.md points to it. A developer may copy the folder to a supported
runtime's user skill directory; the archive does not grant persistent ChatGPT access
or automatically install a plugin. Do not duplicate the full runbook in agent files.

## Primary references

- https://www.testmon.org/ (static-file dependency limitation)
- https://pytest-xdist.readthedocs.io/en/latest/distribution.html
- https://pytest-gremlins.readthedocs.io/en/latest/guide/configuration/
- https://docs.astral.sh/uv/guides/integration/github/
- https://docs.astral.sh/uv/concepts/projects/sync/
- https://prek.j178.dev/configuration/
- https://docs.zizmor.sh/usage/
