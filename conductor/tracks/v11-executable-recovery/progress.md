# Execution ledger — v11-executable-recovery

Baseline: restored complete v10 bundle in an isolated clone. 516 tests passed.
Remote PR #3 remains draft at 126c385d; incomplete tree, no main merge.
Direct DNS and a public native-binary download attempt remain unavailable.

Task 1: complete within contract scope. Six new native regressions failed before implementation; 40 combined native tests now pass. Every redirect is checked before following, and extracted executable reads are bounded. Actual live binary download and Gitleaks execution remain blocked, not certified. Tests mock open_release, the explicit I/O boundary, rather than installing a global URL opener.

Task 2: complete within contract scope. Seven reproducing failures: old success seals survived interrupted reruns/unavailable mutation tools, and non-object cache JSON crashed. Old seals are now consumed during prepare; only complete() after a successful run re-seals. Malformed cache records rebuild cold. 36 combined feedback/integration tests pass. Installed testmon/Gremlins integration remains unexecuted.

Task 3: complete within contract scope. Nine new malformed-manifest/CLI cases failed before implementation (three valid rejection controls already passed). The audit now validates counts, digest strings, canonical paths and original-source identifiers, and emits a failed report for unreadable/invalid/non-object JSON. 32 combined source-contract tests pass. Original public-source acquisition remains incomplete.

Task 4: twenty historical tracks checked in original order; every scoped run returned zero and was committed before the next. All exact commands, counts and SHA-256 log digests are recorded per track. Overlapping counts must not be summed. The v4 cached-feedback implementation checkboxes are now reconciled; installed plugin integration remains blocked.

Integration finding: the first full attempt passed 541 tests but the context gate found a missing new-track metadata file; that file is now supplied. The outer execution timed out before all gates finished; the incomplete receipt/logs are preserved under verification/v11/interrupted-attempt. No full acceptance claim is based on that attempt.

Completed full run: all 30 gates reached on 3140ed37c215fb2e4454faf5da3706d667ec44f7. 541 ordinary tests passed; 7 gates passed, 22 blocked and 1 failed (missing real lock). All receipt log digests matched. The earlier timed-out attempts remain labelled incomplete. This is not installed-tool, hosted or independent acceptance.

Inventory correction: checked v10-acceptance-reconciliation as order21 (9 tests), then recovered the separate remote-only v10-revalidation plan/spec by exact Git blob hash and checked it as order22 (13 tests). Each has a separate commit and receipt. The previous twenty-track count did not include these follow-on records; all22 predecessor records are now reconciled.

Actual remote update ecdc2929653a1710a44ec348edc78be699ea5f74 preserves src/data and contains the complete tests and quality directories. Hashes match the local source. GitHub still lacks some supporting outputs, assets and original ancestry; no complete-migration claim.

Task 6: full execution on committed local source a489f2d610510b822919165a6e3d47f02dfbcde1 reached all30 gates, with541 tests passed,7 gates passed,22 blocked and1 failed. All gate and22 track log digests matched. A separately cloned bundle of this source passed541 tests and git fsck. The local evidence and current status are not claims that the incomplete remote checkout passed.

Task 5 scoped recovery: remote44cc6578d481d9bccf9c9b27e2d9eb057dfe1708 additionally contains exact copies of analyse_v5.py, analyse_v6.py, retrieve_originals.py and six original evidence/parameter files. All retrieved supporting-file hashes and complete src/data/tests/quality subtree hashes match local source. Full supporting artifacts and original ancestry are still not imported.
