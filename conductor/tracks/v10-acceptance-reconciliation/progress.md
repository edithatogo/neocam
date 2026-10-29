# Execution ledger — v10-acceptance-reconciliation

Task 1 complete. Restored v8 full source/history. Found existing draft PR #3 and v9 branch; preserved it. Reconstructed v9 assurance.py, checks.py, cli.py, contracts.py, feedback.py, source_archive.py, analyse_v7.py, ci.yml and test_v9_contracts.py; their Git blob hashes match the connector-returned originals. Ten v9 regression tests passed on the available host. No claim to have authored the remote v9 work in this session.

Ruling: update existing PR #3 rather than create a duplicate; keep draft and do not merge. Full binary/history transfer is still not available through direct Git because DNS fails.

Task 2 complete within local-test scope. Six failing regressions reproduced malformed source-record crashes and historical audit overwrite. Source verification now fails closed on malformed records and accepts an explicit verification-directory output. The unified gate routes source evidence through the selected version. Existing source records/bytes and clinical inputs are unchanged. Combined source/v9 regressions pass; see source_red.txt and source_green.txt.
