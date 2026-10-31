# Conductor tracks — current v14 work

Implementation completion is not external acceptance. Historical tracks remain unchanged under their original folders.

Design authority for the current tracks: [./v14-design.md](./v14-design.md).

## v13 — closed history (unchanged)

---
## [x] Track: Episode/contact semantics
Link: [./tracks/v13-01-contacts/](./tracks/v13-01-contacts/)

---
## [x] Track: Eligible mixed deployment and shared capacity
Link: [./tracks/v13-02-policies/](./tracks/v13-02-policies/)

---
## [x] Track: Clinical plausibility packet and unresolved evidence
Link: [./tracks/v13-03-review/](./tracks/v13-03-review/)

---
## [~] Track: Integrated reproduction, review and private delivery
Link: [./tracks/v13-04-release/](./tracks/v13-04-release/)

Status: implementation effectively complete; final acceptance superseded by the v14 acceptance-integrity track. Historical record only.

## v14 — current work

---
## [~] Track: Engineering rigour — dependency scope, testing depth and static analysis
Link: [./tracks/v14-01-engineering-rigour/](./tracks/v14-01-engineering-rigour/)

Status: dependency audit complete; reportlab incorporation, testing depth, static-analysis depth, experimental trials and the validation spike are being implemented.

---
## [~] Track: Acceptance integrity — source register, artifact manifests and gate-green evidence
Link: [./tracks/v14-02-acceptance-integrity/](./tracks/v14-02-acceptance-integrity/)

Status: source register reconciled; artifact re-seal and full-profile/hosted evidence pending.

---
## [~] Track: Ecosystem integration — sibling repositories, provenance and privacy patterns
Link: [./tracks/v14-03-ecosystem-integration/](./tracks/v14-03-ecosystem-integration/)

Status: inventory complete (11 direct siblings with resolved commits recorded in the design authority). Owner confirmed the `careops-rims` pattern for 3.2; `sourceright` deferred to the roadmap; the VoI alignment task was promoted to its own track.

---
## [~] Track: VoI integration with voiage
Link: [./tracks/v14-04-voi-voiage-integration/](./tracks/v14-04-voi-voiage-integration/)

Status: owner-prioritised. `voiage` becomes the VoI engine; capabilities unique to `vop_poc_nz` are ported into `voiage` (never a dependency here); a voiage release that installs on Python 3.15 gates the downstream integration. Corrected finding: voiage `main` is already 3.15-ready and allows pyarrow 26 — the published 2.2.0 tag lags — so the blocker is a release, not a code change.
