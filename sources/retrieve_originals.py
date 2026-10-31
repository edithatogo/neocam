# ruff: ignore[implicit-namespace-package] -- sources/ is a retrieval directory run as a script, not an installed package
"""Opt-in bounded original-source retrieval. No execution is implied by its presence."""

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import IO, TYPE_CHECKING, override

if TYPE_CHECKING:
    from email.message import Message

ROOT = Path(__file__).resolve().parent
TARGETS = {
    "NEP26.pdf": "https://www.ihacpa.gov.au/sites/default/files/2026-03/national_efficient_price_determination_2026-27_2.pdf",
    "NEP26_price_weights.xlsx": "https://www.ihacpa.gov.au/sites/default/files/2026-03/National_Efficient_Price_Determination_2026-27_Price_Weight_Tables.XLSX",
    "NHRA_2026_2031.pdf": "https://federalfinancialrelations.gov.au/sites/federalfinancialrelations.gov.au/files/2026-04/nhra-2026-31-addendum-consolidated.pdf",
    "QH_births_2022.pdf": "https://www.health.qld.gov.au/__data/assets/pdf_file/0020/1378010/8-fac2022x.pdf",
}
ALLOWED = {"www.ihacpa.gov.au", "federalfinancialrelations.gov.au", "www.health.qld.gov.au"}
ALLOWED_PORTS = {None, 443}
MAX_RESPONSE_BYTES = 20_000_000
PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK"


def approved_url(url: str) -> str:
    """Return the unchanged URL when it points at an approved HTTPS source.

    A redirect can only leave the approved set through a host, scheme or port the
    helper rejects, so the destination is checked before any request is sent.

    Returns:
        The URL, unchanged, when it is an approved HTTPS source.

    Raises:
        ValueError: If the URL is not an approved HTTPS source.
    """
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED or u.username or u.password or u.port not in ALLOWED_PORTS:
        msg = "Unapproved source or redirect"
        raise ValueError(msg)
    return url


class ApprovedRedirect(urllib.request.HTTPRedirectHandler):
    """Reject an unapproved destination before urllib sends a redirected request."""

    @override
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Guard a redirect by checking its destination host before it is sent.

        Parameters:
            req: The original request that produced the redirect.
            fp: The file-like object of the redirecting response.
            code: The HTTP status code of the redirect.
            msg: The reason phrase of the redirect.
            headers: The response headers.
            newurl: The destination URL, verified before any request is sent.

        Returns:
            The redirect request built by urllib, or ``None`` when it declines one.
        """
        approved_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def main() -> None:
    """Print the approved targets, or fetch each one and write retrieval receipts.

    Without ``--fetch`` the target table is printed and nothing is downloaded. With
    ``--fetch`` each target is retrieved once, signature-checked, written under
    ``original/`` and recorded in ``retrieval_receipts.json``.

    Raises:
        ValueError: If a target is not an approved HTTPS source, or its response is
            oversized or lacks the expected original file signature.
    """
    p = argparse.ArgumentParser()
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()
    if not a.fetch:
        print(json.dumps(TARGETS, indent=2))  # ruff: ignore[print] -- CLI target list goes to stdout
        return
    receipts = []
    (ROOT / "original").mkdir(exist_ok=True)
    for name, url in TARGETS.items():
        try:  # ruff: ignore[too-many-statements-in-try-clause] -- one bounded fetch-and-validate per target becomes this target's receipt
            approved_url(url)
            opener = urllib.request.build_opener(ApprovedRedirect())
            with opener.open(url, timeout=12) as response:
                approved_url(response.url)
                data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                msg = "Oversized response"
                raise ValueError(msg)  # ruff: ignore[raise-within-try] -- the failure is recorded as this target's receipt
            if not data.startswith(PDF_SIGNATURE if name.endswith(".pdf") else ZIP_SIGNATURE):
                msg = "Expected original file signature not HTML"
                raise ValueError(msg)  # ruff: ignore[raise-within-try] -- the failure is recorded as this target's receipt
            target = ROOT / "original" / name
            target.write_bytes(data)
            receipts.append({
                "file": name,
                "url": url,
                "status": "saved",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        except (OSError, ValueError) as e:
            receipts.append({"file": name, "url": url, "status": "failed", "reason": str(e)[:250]})
    (ROOT / "retrieval_receipts.json").write_text(json.dumps(receipts, indent=2))
    print(json.dumps(receipts, indent=2))  # ruff: ignore[print] -- CLI receipt report goes to stdout


if __name__ == "__main__":
    main()
