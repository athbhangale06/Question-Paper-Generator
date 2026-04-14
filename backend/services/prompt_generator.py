import json

try:
    from backend.services.file_processor import process_document_for_ai
except ImportError:
    from services.file_processor import process_document_for_ai


def _format_sections_for_instruction(sections):
    active_sections = [section for section in sections if isinstance(section, dict) and section.get("enabled", True)]
    if not active_sections:
        return ""

    lines = []
    total_section_marks = 0

    for index, section in enumerate(active_sections, start=1):
        section_id = str(section.get("id", index)).strip() or str(index)
        section_type = str(section.get("type", f"Section {index}")).strip()
        count = int(section.get("count", 0) or 0)
        marks = int(section.get("marks", 0) or 0)
        section_total = count * marks
        total_section_marks += section_total
        lines.append(
            f"Section {section_id}: {section_type} | {count} questions | {marks} marks each | {section_total} total marks"
        )

    lines.append(
        f"IMPORTANT: Generate the COMPLETE paper for all sections above. Do not stop early, do not omit any section, and ensure the full paper covers {total_section_marks} marks across the configured sections."
    )
    return "\n".join(lines)


def build_payload(data):
    subject = data.get("subject", "General")
    grade = data.get("grade", "Unknown")
    board = data.get("board", "")
    difficulty = data.get("difficulty", "Medium")
    marks = data.get("totalMarks", data.get("marks", 50))
    custom = data.get("prompt", data.get("custom_prompt", ""))
    sections = data.get("sections", [])
    topic = data.get(
        "topic",
        data.get("query", data.get("keyword", data.get("custom_prompt", data.get("prompt", subject)))),
    )
    file_path = data.get("file_path", data.get("pdf_path", ""))

    # --- Clean values ---
    subject = str(subject).strip()
    grade = str(grade).strip()
    board = str(board).strip()
    difficulty = str(difficulty).strip()
    custom = str(custom).strip()
    topic = str(topic).strip()
    file_path = str(file_path).strip()

    try:
        marks = int(marks)
    except Exception:
        marks = 50

    if isinstance(sections, str):
        try:
            sections = json.loads(sections)
        except json.JSONDecodeError:
            sections = []

    if not isinstance(sections, list):
        sections = []

    sections_instruction = _format_sections_for_instruction(sections)

    retrieval_topic = custom or topic or subject

    document_data = process_document_for_ai(file_path, retrieval_topic) if file_path else {
        "file_path": file_path,
        "file_type": "",
        "text": "",
        "chunks": [],
        "compressed_chunks": [],
        "selected_chunks": [],
        "summaries": [],
        "context": "",
        "ocr_used": False,
    }

    selected_chunks = document_data["summaries"][:2] if document_data["summaries"] else []
    if not selected_chunks and document_data["selected_chunks"]:
        selected_chunks = document_data["selected_chunks"][:2]
    if not selected_chunks and document_data["compressed_chunks"]:
        selected_chunks = document_data["compressed_chunks"][:1]
    if not selected_chunks and document_data["chunks"]:
        selected_chunks = document_data["chunks"][:1]

    file_content = "\n\n".join(chunk.strip() for chunk in selected_chunks if chunk).strip()
    if len(file_content) > 1800:
        file_content = file_content[:1800].rsplit(" ", 1)[0].strip()

    title = f"{subject or 'General'} - {grade or 'General'} Question Paper"
    
    if custom:
        strong_instruction = (
            "CRITICAL DIRECTIVE: You MUST strictly adhere to the following user instructions. "
            "If the user specifies an institute name, university, or header, you MUST include it in a 'header' field at the top level of the JSON. "
            "If the user specifies a time or duration, you MUST include it in a 'time' field at the top level of the JSON. "
            "If the user specifies exact section layouts (e.g., 'Q1 A or Q1 B', specific marks, optional questions), "
            "you MUST format the 'sections' array exactly as requested without any deviation. "
            "You MUST return the FULL question paper, not a partial paper, and the total output must satisfy the requested structure and marks.\n\n"
            f"USER INSTRUCTIONS:\n{custom}"
        )
        custom_instruction = strong_instruction
    else:
        custom_instruction = f"Generate a complete {subject} question paper for {grade}."

    if sections_instruction:
        custom_instruction = f"{custom_instruction}\n\nSECTION REQUIREMENTS:\n{sections_instruction}"

    # --- Final n8n-ready payload ---
    payload = {
        "title": title,
        "subject": subject,
        "marks": marks,
        "total_marks": marks,
        "grade": grade,
        "board": board,
        "difficulty": difficulty,
        "custom_instruction": custom_instruction,
        "user_instructions": custom_instruction,
        "topic": retrieval_topic,
        "sections": sections,
        "section_requirements": sections_instruction,
        "file_content": file_content,
        "reference_content": file_content,
        "source_type": document_data["file_type"],
        "has_reference_content": bool(file_content),
        "ocr_used": bool(document_data["ocr_used"]),
    }

    debug = {
        "sections": sections,
        "retrieval_topic": retrieval_topic,
        "source_document": {
            "file_path": document_data["file_path"],
            "file_type": document_data["file_type"],
            "text": document_data["text"],
            "chunks": document_data["chunks"],
            "compressed_chunks": document_data["compressed_chunks"],
            "selected_chunks": document_data["selected_chunks"],
            "summaries": document_data["summaries"],
            "context": document_data["context"],
            "ocr_used": document_data["ocr_used"],
        },
    }

    return payload, debug
