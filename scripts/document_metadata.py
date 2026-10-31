# ruff: ignore[implicit-namespace-package] -- scripts/ ships no package __init__
"""Neutralise OOXML document metadata so generated documents carry no personal author.

Why this exists
---------------
The templates under ``assets/`` and the supplied originals under ``sources/original/``
are authentic corporate Office files. Their ``docProps/core.xml`` ``dc:creator`` and
``cp:lastModifiedBy`` name the people who last edited them, and their
``docProps/app.xml`` ``Company``/``Template`` name the organisation. python-docx and
python-pptx preserve those parts when a generator fills a template, so every generated
``.docx``/``.pptx`` inherited the names. The privacy gate deliberately does not detect
personal names, so this passed silently.

What this does
--------------
:func:`neutralise_core_properties` sets the library-exposed core properties to a neutral
project value, and :func:`neutralise_archive_metadata` performs a deterministic pass over
the saved container that also covers ``docProps/app.xml`` and any workbook an authoring
library writes without a core-properties API. :func:`save_neutralised` is the one call a
generator makes for a python-docx/python-pptx object.

Historical tracked artefacts are retention evidence and are deliberately **not** rewritten;
``verification/v13/burndown/document-metadata.md`` records how many still carry a name.
"""

from __future__ import annotations

import re
import zipfile
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# One neutral project value replaces every personal or organisation-identifying field.
NEUTRAL_AUTHOR = "Neocam evaluation"
NEUTRAL_COMPANY = "Neocam evaluation"
# The extended-properties template name has no neutral project equivalent; it is cleared.
NEUTRAL_TEMPLATE = ""

CORE_PART = "docProps/core.xml"
APP_PART = "docProps/app.xml"
# Core properties that name a person; the free-text fields are cleared because a
# corporate template may have filled them with a name or an organisation.
_CORE_NAME_FIELDS = ("creator", "lastModifiedBy")
_CORE_FREE_FIELDS = ("description", "keywords", "contentStatus", "category", "identifier", "language", "subject")
# ``docProps/app.xml`` fields that name an organisation or a corporate template.
_APP_NAME_FIELDS = ("Company", "Manager")
_APP_TEMPLATE_FIELDS = ("Template",)


class CoreProperties(Protocol):
    """The settable core-property surface shared by python-docx and python-pptx."""

    author: str
    category: str
    comments: str
    content_status: str
    identifier: str
    keywords: str
    language: str
    last_modified_by: str
    subject: str


class NeutralisableDocument(Protocol):
    """A python-docx document or python-pptx presentation that can save itself."""

    @property
    def core_properties(self) -> CoreProperties:
        """The document core properties."""
        ...

    def save(self, path: str) -> None:
        """Write the document to ``path``."""
        ...


def neutralise_core_properties(properties: object) -> None:
    """Replace every identity-bearing core property with the neutral project value.

    Args:
        properties: The core properties of a python-docx document or python-pptx
            presentation, exposed as ``document.core_properties``. The parameter is
            taken as ``object`` because the two libraries expose unrelated
            ``CoreProperties`` classes; the cast is to the shared structural surface.
    """
    core = cast("CoreProperties", properties)
    core.author = NEUTRAL_AUTHOR
    core.last_modified_by = NEUTRAL_AUTHOR
    core.comments = ""
    core.category = ""
    core.content_status = ""
    core.identifier = ""
    core.keywords = ""
    core.language = ""
    core.subject = ""


def _element_pattern(local_name: str) -> re.Pattern[str]:
    """Return a pattern matching one element by local name under any namespace prefix.

    Returns:
        re.Pattern[str]: A pattern with the open tag, content and close tag as groups.
    """
    return re.compile(rf"(<(?:\w+:)?{local_name}\b[^>]*>)(.*?)(</(?:\w+:)?{local_name}>)", re.DOTALL)


def _escape(value: str) -> str:
    """Escape text for an XML character-data position.

    Returns:
        str: The value with the XML metacharacters escaped.
    """
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _replace_element(text: str, local_name: str, value: str) -> str:
    """Return ``text`` with every named element's character data replaced by ``value``.

    Returns:
        str: The rewritten XML text.
    """
    return _element_pattern(local_name).sub(lambda match: match.group(1) + _escape(value) + match.group(3), text)


def _neutralise_core_xml(data: bytes) -> bytes:
    """Return the core-properties XML with every name and free-text field neutralised.

    Returns:
        bytes: The rewritten ``docProps/core.xml`` payload.
    """
    text = data.decode("utf-8")
    for field in _CORE_NAME_FIELDS:
        text = _replace_element(text, field, NEUTRAL_AUTHOR)
    for field in _CORE_FREE_FIELDS:
        text = _replace_element(text, field, "")
    return text.encode("utf-8")


def _neutralise_app_xml(data: bytes) -> bytes:
    """Return the extended-properties XML with organisation and template neutralised.

    Returns:
        bytes: The rewritten ``docProps/app.xml`` payload.
    """
    text = data.decode("utf-8")
    for field in _APP_NAME_FIELDS:
        text = _replace_element(text, field, NEUTRAL_COMPANY)
    for field in _APP_TEMPLATE_FIELDS:
        text = _replace_element(text, field, NEUTRAL_TEMPLATE)
    return text.encode("utf-8")


_PART_REWRITERS: dict[str, Callable[[bytes], bytes]] = {
    CORE_PART: _neutralise_core_xml,
    APP_PART: _neutralise_app_xml,
}


def neutralise_archive_metadata(path: Path) -> bool:
    """Rewrite the metadata parts of a saved OOXML container to neutral values.

    The container is read member by member and written back with the original member
    order, compression and timestamps, so only the changed metadata parts differ from
    the library's own output.

    Args:
        path: The saved ``.docx``/``.pptx``/``.xlsx`` file to neutralise in place.

    Returns:
        bool: True when the archive was rewritten, False when it already carried no
        personal or organisation value.
    """
    with zipfile.ZipFile(path) as archive:
        members = [(info, archive.read(info.filename)) for info in archive.infolist()]
    rewrite = _PART_REWRITERS
    rewritten = [(info, rewrite[info.filename](data) if info.filename in rewrite else data) for info, data in members]
    if rewritten == members:
        return False
    temporary = path.with_name(path.name + ".neutral")
    with zipfile.ZipFile(temporary, "w") as archive:
        for info, data in rewritten:
            archive.writestr(info, data)
    _ = temporary.replace(path)
    return True


def save_neutralised(document: object, path: Path) -> None:
    """Neutralise core properties, save the document, then strip residual metadata.

    Args:
        document: A python-docx document or python-pptx presentation; taken as
            ``object`` and cast to the shared save-and-core-properties surface because
            the two libraries expose unrelated concrete types.
        path: Destination file path.
    """
    target = cast("NeutralisableDocument", document)
    neutralise_core_properties(target.core_properties)
    target.save(str(path))
    _ = neutralise_archive_metadata(path)
