# Execution ledger — v10-acceptance-reconciliation

Task 1 complete. Restored v8 full source/history. Found existing draft PR #3 and v9 branch; preserved it. Reconstructed v9 assurance.py, checks.py, cli.py, contracts.py, feedback.py, source_archive.py, analyse_v7.py, ci.yml and test_v9_contracts.py; their Git blob hashes match the connector-returned originals. Ten v9 regression tests passed on the available host. No claim to have authored the remote v9 work in this session.

Ruling: update existing PR #3 rather than create a duplicate; keep draft and do not merge. Full binary/history transfer is still not available through direct Git because DNS fails.

Task 2 complete within local-test scope. Six failing regressions reproduced malformed source-record crashes and historical audit overwrite. Source verification now fails closed on malformed records and accepts an explicit verification-directory output. The unified gate routes source evidence through the selected version. Existing source records/bytes and clinical inputs are unchanged. Combined source/v9 regressions pass; see source_red.txt and source_green.txt.

Task 3 complete within current-host regression scope. Twenty historical tracks, including the newly discovered remote v9 track, were checked sequentially. Each record and its scoped log was committed before moving on. All selected test groups passed. Counts overlap; full-suite count is determined separately. Remaining clinical, archival, dependency, security and hosted requirements stay open.

Task 4 complete as an execution, not successful acceptance. The completed unified run enumerated 30 required gates: 7 passed, 22 blocked, 1 failed; 513 ordinary tests passed. The failed gate rejects the absent real uv.lock. All receipt log digests matched. The prior interrupted run remains separately labelled.

Task 5 partial. Imported original native-tool/bootstrap/prek/Vale/Gitleaks/Renovate configuration and the source-audit repairs into draft PR #3 using two verified ref updates. The full source/history/binary migration is not complete. Latest hosted attempt failed before runner allocation; no cause inferred.

Concurrent change reconciled. The feature branch advanced to cb01184 (correct testmon.pytest_testmon import and three tests) and then 3021017 (additional recovered source/tests). Both updates were preserved in remote commit 737b5e9 with a non-force leased update. The four plugin-change files match the remote Git blob IDs. One failing and two passing new tests were reproduced before integrating the plugin fix; all 35 selected integration regressions then passed. This is a configuration/contract check, not execution of the unavailable testmon package.
