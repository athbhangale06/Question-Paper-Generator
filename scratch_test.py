import json
import os
import sys

from backend.services.document_exporter import create_docx_from_n8n_response

payload = {
    "title": "Computer Networks Test",
    "subject": "Computer Networks",
    "grade": "Under Graduate",
    "total_marks": 100,
    "sections": []
}

create_docx_from_n8n_response(payload, ".", "test.docx", "Test")
print("Done")
