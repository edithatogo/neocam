# Task Workflow
1. Resolve context through index.md and read selected spec/plan. Registry statuses are [ ], [~], [x].
2. Mark the selected task in progress; reproduce its defect/absent behaviour with a failing test. Store red evidence under verification/v13.
3. Implement the smallest dependency-free change. Run scoped tests and record green evidence. Commit task code/tests and record commit in progress ledger.
4. Invoke conductor-review for the explicit task/track diff: intent, correctness, numerical units, safety, privacy and test adequacy. Apply fixes, retest and reconcile track.
5. [x] denotes the specified implementation scope only. External installation, human/independent review, full GitHub migration and source acquisition stay explicit, separately gated blockers.
6. Finalise fingerprinted context, generate and seal new outputs, commit; then run unified assurance and append actual status only under verification/handoff. Do not edit fingerprinted inputs after final assurance.

User authorised implementation and review fixes; no repeated confirmations are needed. Keep existing historical tracks, no deletion/archive, no force push/main merge. Source remains NumPy/stdlib with Polars-only DataFrame policy. No missing tool becomes a pass. Same-assistant review is not independent validation.
