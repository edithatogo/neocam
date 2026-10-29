# Execution ledger — v11-executable-recovery

Baseline: restored complete v10 bundle in an isolated clone. 516 tests passed.
Remote PR #3 remains draft at 126c385d; incomplete tree, no main merge.
Direct DNS and a public native-binary download attempt remain unavailable.

Task 1: complete within contract scope. Six new native regressions failed before implementation; 40 combined native tests now pass. Every redirect is checked before following, and extracted executable reads are bounded. Actual live binary download and Gitleaks execution remain blocked, not certified. Tests mock open_release, the explicit I/O boundary, rather than installing a global URL opener.

Task 2: complete within contract scope. Seven reproducing failures: old success seals survived interrupted reruns/unavailable mutation tools, and non-object cache JSON crashed. Old seals are now consumed during prepare; only complete() after a successful run re-seals. Malformed cache records rebuild cold. 36 combined feedback/integration tests pass. Installed testmon/Gremlins integration remains unexecuted.

Task 3: complete within contract scope. Nine new malformed-manifest/CLI cases failed before implementation (three valid rejection controls already passed). The audit now validates counts, digest strings, canonical paths and original-source identifiers, and emits a failed report for unreadable/invalid/non-object JSON. 32 combined source-contract tests pass. Original public-source acquisition remains incomplete.
