"""A partial model receipt must never masquerade as full release assurance."""

from scripts import verify


def test_model_receipt_is_not_full_release() -> None:
    assert not verify.release_assurance_complete([{"gate": "pytest", "status": "passed"}], "model")


def test_release_receipt_requires_all_gates() -> None:
    assert not verify.release_assurance_complete([{"gate": "pytest", "status": "passed"}], "release")


def test_release_receipt_requires_no_blocked_gate() -> None:
    gates = [{"gate": name, "status": "passed"} for name in verify.RELEASE_GATES]
    assert verify.release_assurance_complete(gates, "release")
    gates[-1]["status"] = "blocked"
    assert not verify.release_assurance_complete(gates, "release")
