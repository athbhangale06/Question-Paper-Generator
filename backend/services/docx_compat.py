"""Centralized python-docx imports with a clearer failure message."""

try:
    from docx import Document
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    from docx.shared import Pt
except Exception as exc:
    raise ImportError(
        "DOCX support requires the 'python-docx' package. "
        "If you installed 'docx', uninstall it first, then install 'python-docx'."
    ) from exc

