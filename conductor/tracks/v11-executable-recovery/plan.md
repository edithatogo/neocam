# v11: finish scoped repairs before adding features

Existing project and PR #3 are authoritative. No scientific input changes, feature expansion,
force push, main merge, blanket suppression, false lock or independent-review claim.
Dedicated restored clone: /mnt/data/neocam-v11. Starting local commit 139b4b2.
Starting remote PR head 126c385d5894a2f3c8b9534a4095cd784b8bf18e.

Execute in this order and commit each implementation with fresh scoped evidence:
1. [x] Dependencies/native security: reject unapproved redirects and oversized extracted executables.
2. [x] Cached development: consume previous success seals before starting a new run; fail closed on malformed cache metadata.
3. [x] Source provenance: validate manifest fields and failure reports without exception leaks or unsupported completeness.
4. [x] Historical tracks: reconcile the original twenty, then the two v10 follow-on records (one recovered from GitHub); preserve unresolved external/scientific acceptance.
5. [x] Selected repository recovery: the complete 39-file tests directory and repaired quality code are pushed to PR #3 at ecdc292. Their subtree hashes match the tested local source. Supporting driver/evidence recovery is being completed separately; full migration remains open.
6. [ ] Full run on 3140ed3 completed: 541 tests; 7 passed gates, 22 blocked, 1 failed. Recheck the final documented source, restore and test the final package.

Dependencies: native mocks must still prove extraction without a network; cache tests never replace
installed-plugin acceptance; source audit must remain unsuccessful for an empty scope; full
assurance consumes the repaired code but cannot certify absent tools or an incomplete remote tree.

Ruling: prior track-scoped tests are historical evidence, not proof that every original checklist item
is implemented. No additional clinical feature is authorised by this engineering pass.
