# VoI integration with voiage (owner-prioritised)

Design authority: [../../v14-design.md](../../v14-design.md).
Implementation scope: make the owner's VoI engine `edithatogo/voiage` the single source of
value-of-information and value-of-perspective semantics for this project; port the
capabilities that exist only in `edithatogo/vop_poc_nz` into voiage (never as a dependency
here); then consume voiage from this model with parity evidence against the current
hand-rolled implementation. `vop_poc_nz` is an **evidence source only** — it is not and
must not become a dependency of this repository.

Numerical discipline: if voiage's results differ from the current hand-rolled EVPI/VoP
values, the difference is a finding to surface and disclose, not something to absorb
silently. Published numbers must not move without their own review.
