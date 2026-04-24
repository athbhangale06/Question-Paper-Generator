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
    incoming_document = data.get("document", {})
    topic = data.get(
        "topic",
        data.get("query", data.get("keyword", data.get("custom_prompt", data.get("prompt", subject)))),
    )
    file_paths = data.get("file_paths", []) or ([data.get("file_path")] if data.get("file_path") else ([data.get("pdf_path")] if data.get("pdf_path") else []))
    document_names = data.get("document_names", []) or ([data.get("document_name")] if data.get("document_name") else [])

    # --- Clean values ---
    subject = str(subject).strip()
    grade = str(grade).strip()
    board = str(board).strip()
    difficulty = str(difficulty).strip()
    custom = str(custom).strip()
    topic = str(topic).strip()
    file_paths = [str(p).strip() for p in file_paths if str(p).strip()]
    document_names = [str(n).strip() for n in document_names if str(n).strip()]

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

    all_document_data = []
    combined_file_content = ""
    combined_text = ""

    for fp in file_paths:
        doc_data = process_document_for_ai(fp, retrieval_topic) if fp else None
        if doc_data:
            all_document_data.append(doc_data)
            sel_chunks = doc_data.get("summaries", [])[:2] if doc_data.get("summaries") else []
            if not sel_chunks and doc_data.get("selected_chunks"):
                sel_chunks = doc_data.get("selected_chunks")[:2]
            if not sel_chunks and doc_data.get("compressed_chunks"):
                sel_chunks = doc_data.get("compressed_chunks")[:1]
            if not sel_chunks and doc_data.get("chunks"):
                sel_chunks = doc_data.get("chunks")[:1]
                
            fc = "\n\n".join(chunk.strip() for chunk in sel_chunks if chunk).strip()
            if fc:
                combined_file_content += f"\n\n--- Source File ---\n{fc}"
            if doc_data.get("text"):
                combined_text += f"\n\n{doc_data['text']}"

    combined_file_content = combined_file_content.strip()
    combined_text = combined_text.strip()
    if len(combined_file_content) > 3000:
        combined_file_content = combined_file_content[:3000].rsplit(" ", 1)[0].strip()

    incoming_document_name = ""
    incoming_document_content = ""
    if isinstance(incoming_document, dict):
        incoming_document_name = str(incoming_document.get("name", "")).strip()
        incoming_document_content = str(incoming_document.get("content", "")).strip()

    resolved_document_name = (
        incoming_document_name
        or (", ".join(document_names) if document_names else "")
        or (file_paths[0].split("\\")[-1] if file_paths else "")
    )
    
    extracted_text = str(
        data.get("file_content") 
        or incoming_document_content 
        or combined_file_content 
        or combined_text 
        or ""
    ).strip()

    if len(extracted_text) > 2000:
        extracted_text = extracted_text[:2000].rsplit(" ", 1)[0] + "..."


    # Format Syllabus metadata if available
    syllabus_metadata = data.get("syllabus_metadata", {})
    syllabus_file_content = syllabus_metadata.get("fileContent", "")
    
    # Prioritize what syllabus parser gave us
    if syllabus_file_content:
        extracted_text = syllabus_file_content
    else:
        # Fallback to the old formatting if for some reason fileContent is missing from metadata
        if syllabus_metadata:
            syllabus_injection = "\n\n[SYLLABUS CONTEXT]\n"
            if syllabus_metadata.get("subject"):
                syllabus_injection += f"Syllabus Subject: {syllabus_metadata['subject']}\n"
            if syllabus_metadata.get("topics"):
                syllabus_injection += "Key Topics: " + ", ".join(syllabus_metadata['topics']) + "\n"
            if syllabus_metadata.get("units"):
                syllabus_injection += "Modules/Units:\n"
                for u in syllabus_metadata["units"][:5]:
                    syllabus_injection += f"- {u.get('name', 'Module')}\n"
                    if u.get('topics'):
                        syllabus_injection += "   Topics: " + ", ".join(u['topics'][:5]) + "\n"
            if syllabus_metadata.get("course_outcomes"):
                syllabus_injection += "Course Outcomes:\n" + "\n".join([f"- {co}" for co in syllabus_metadata['course_outcomes']])
                
            extracted_text = syllabus_injection.strip() + "\n\n" + extracted_text
            extracted_text = extracted_text.strip()

    payload = {
        "subject": data.get("subject"),
        "marks": int(data.get("marks", 0)) if data.get("marks") else 0,
        "grade": data.get("grade"),
        "board": data.get("board"),
        "difficulty": data.get("difficulty"),
        "custom_instruction": custom,
        "fileContent": extracted_text
    }

    debug = {
        "sections": sections,
        "retrieval_topic": retrieval_topic,
        "section_requirements": sections_instruction,
        "document_preview": combined_file_content,
        "source_document": {
            "file_paths": file_paths,
            "text": combined_text,
            "context": combined_file_content,
            "parsed_files": len(all_document_data),
        },
    }

    return payload, debug
