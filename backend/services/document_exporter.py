import json
import os
import re
from typing import Any, Dict, List, Optional

if __package__:
    from .docx_compat import Document, Pt, WD_PARAGRAPH_ALIGNMENT
else:
    from backend.services.docx_compat import Document, Pt, WD_PARAGRAPH_ALIGNMENT


def _stringify(value: Any, depth: int = 0) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = []
        if "option_label" in value:
            parts.append(f"Option {value['option_label']}:")
        if "question_part" in value:
            parts.append(f"({value['question_part']})")
        
        qt = value.get("question") or value.get("question_text") or value.get("text")
        if qt and not isinstance(qt, (dict, list)):
            parts.append(str(qt))
            
        if "marks" in value:
            parts.append(f"[{value['marks']} Marks]")
            
        if "sub_questions" in value and isinstance(value["sub_questions"], list):
            sub_texts = [_stringify(sq, depth + 1) for sq in value["sub_questions"]]
            indent = "  " * (depth + 1)
            parts.append("\n" + "\n".join(f"{indent}{sq}" for sq in sub_texts))
            
        if parts:
            return " ".join(parts).replace(" \n", "\n").replace("\n ", "\n").strip()
            
        lines = []
        for k, v in value.items():
            lines.append(f"{str(k).replace('_', ' ').title()}: {_stringify(v, depth + 1)}")
        return "\n".join(lines)
        
    if isinstance(value, list):
        bullet = "•" if depth == 0 else "-"
        indent = "  " * depth
        return "\n".join(f"{indent}{bullet} {_stringify(item, depth + 1)}" for item in value)

    return str(value).strip()


def parse_n8n_body(raw_body: str) -> Any:
    if not raw_body:
        return {}

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        cleaned = _strip_markdown_code_fences(raw_body.strip())
        reparsed = _parse_json_candidate(cleaned)
        return reparsed if reparsed is not cleaned else cleaned


def _strip_markdown_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _parse_json_candidate(text: str) -> Any:
    cleaned = _strip_markdown_code_fences(text)
    if not cleaned:
        return text

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    first_object = cleaned.find("{")
    last_object = cleaned.rfind("}")
    if first_object != -1 and last_object > first_object:
        candidate = cleaned[first_object:last_object + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_array = cleaned.find("[")
    last_array = cleaned.rfind("]")
    if first_array != -1 and last_array > first_array:
        candidate = cleaned[first_array:last_array + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return text


def _maybe_parse_json_string(value: str) -> Any:
    text = _strip_markdown_code_fences(_stringify(value))
    if not text:
        return value

    if not ((text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]"))):
        parsed_candidate = _parse_json_candidate(text)
        return parsed_candidate if parsed_candidate is not text else value

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        parsed_candidate = _parse_json_candidate(text)
        return parsed_candidate if parsed_candidate is not text else value


def _extract_nested_payload(value: Any) -> Any:
    if isinstance(value, str):
        parsed = _maybe_parse_json_string(value)
        if parsed is not value:
            return _extract_nested_payload(parsed)
        return value

    if isinstance(value, list):
        for item in value:
            extracted = _extract_nested_payload(item)
            if _is_question_paper_payload(extracted):
                return extracted
        return value

    if isinstance(value, dict):
        if _is_question_paper_payload(value):
            return value

        content = value.get("content")
        if isinstance(content, dict):
            parts = content.get("parts")
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        extracted = _extract_nested_payload(part.get("text"))
                        if _is_question_paper_payload(extracted):
                            return extracted

        candidates = value.get("candidates")
        if isinstance(candidates, list):
            for candidate in candidates:
                extracted = _extract_nested_payload(candidate)
                if _is_question_paper_payload(extracted):
                    return extracted

        parts = value.get("parts")
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict):
                    extracted = _extract_nested_payload(part.get("text"))
                    if _is_question_paper_payload(extracted):
                        return extracted

        text_value = value.get("text")
        if text_value:
            extracted = _extract_nested_payload(text_value)
            if _is_question_paper_payload(extracted):
                return extracted

    return value


def _is_question_paper_payload(data: Any) -> bool:
    return isinstance(data, dict) and (
        "sections" in data
        or "general_instructions" in data
        or "title" in data
        or "subject" in data
    )


def _get_first_non_empty(mapping: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        value = _stringify(mapping.get(key))
        if value:
            return value
    return ""


def _normalize_question(question: Any, index: int) -> Dict[str, Any]:
    if not isinstance(question, dict):
        text = _stringify(question)
        return {
            "question_number": str(index),
            "type": "",
            "question_text": text,
            "options": [],
            "answer": "",
            "marks": "",
        }

    options = question.get("options", [])
    if not isinstance(options, list):
        options = []

    return {
        "question_number": _get_first_non_empty(question, ["question_number", "number", "id"]) or str(index),
        "type": _get_first_non_empty(question, ["type", "question_type"]),
        "question_text": _get_first_non_empty(question, ["question_text", "question", "text", "prompt"]),
        "options": [_stringify(option) for option in options if _stringify(option)],
        "answer": _get_first_non_empty(question, ["answer", "correct_answer"]),
        "marks": _get_first_non_empty(question, ["marks", "score"]),
    }


def _normalize_section(section: Any, index: int) -> Dict[str, Any]:
    if not isinstance(section, dict):
        return {
            "title": f"Section {index}",
            "instructions": "",
            "marks_distribution": "",
            "questions": [_normalize_question(section, 1)],
        }

    questions = section.get("questions", [])
    if not isinstance(questions, list):
        questions = []

    return {
        "title": _get_first_non_empty(section, ["title", "name"]) or f"Section {index}",
        "instructions": _get_first_non_empty(section, ["instructions"]),
        "marks_distribution": _get_first_non_empty(section, ["marks_distribution", "total_marks"]),
        "type": _get_first_non_empty(section, ["type"]),
        "questions": [_normalize_question(question, q_index) for q_index, question in enumerate(questions, start=1)],
    }


def _normalize_question_paper(data: Any, fallback_title: str = "") -> Dict[str, Any]:
    extracted = _extract_nested_payload(data)

    if not isinstance(extracted, dict):
        return {
            "title": fallback_title or "Generated Question Paper",
            "subject": "",
            "grade": "",
            "total_marks": "",
            "paper_type": "",
            "difficulty": "",
            "general_instructions": [],
            "sections": [],
            "note": _stringify(extracted),
        }

    sections = extracted.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    general_instructions = extracted.get("general_instructions", [])
    if not isinstance(general_instructions, list):
        general_instructions = []

    title = _get_first_non_empty(extracted, ["title"])
    if title and title.strip().startswith("{") and title.strip().endswith("}"):
        title = fallback_title or "Generated Question Paper"
    elif not title:
        title = fallback_title or "Generated Question Paper"

    return {
        "title": title,
        "header": _get_first_non_empty(extracted, ["header", "institute", "university", "college"]),
        "time": _get_first_non_empty(extracted, ["time", "duration", "time_allowed"]),
        "subject": _get_first_non_empty(extracted, ["subject"]),
        "grade": _get_first_non_empty(extracted, ["grade"]),
        "total_marks": _get_first_non_empty(extracted, ["total_marks", "marks"]),
        "paper_type": _get_first_non_empty(extracted, ["paper_type"]),
        "difficulty": _get_first_non_empty(extracted, ["difficulty"]),
        "general_instructions": [_stringify(item) for item in general_instructions if _stringify(item)],
        "sections": [_normalize_section(section, index) for index, section in enumerate(sections, start=1)],
        "note": _get_first_non_empty(extracted, ["note"]),
    }


def normalize_question_paper(data: Any, fallback_title: str = "") -> Dict[str, Any]:
    return _normalize_question_paper(data, fallback_title=fallback_title)


def _append_if_text(lines: List[str], text: Any, prefix: str = "") -> None:
    value = _stringify(text)
    if value:
        lines.append(f"{prefix}{value}")


def build_preview_text(n8n_response: Any) -> str:
    paper = _normalize_question_paper(n8n_response)
    lines: List[str] = []

    _append_if_text(lines, paper["title"])

    meta = " | ".join(
        item
        for item in [
            paper["subject"] and f"Subject: {paper['subject']}",
            paper["grade"] and f"Grade: {paper['grade']}",
            paper["total_marks"] and f"Total Marks: {paper['total_marks']}",
            paper["paper_type"] and f"Paper Type: {paper['paper_type']}",
            paper["difficulty"] and f"Difficulty: {paper['difficulty']}",
        ]
        if item
    )
    _append_if_text(lines, meta)

    if lines:
        lines.append("")

    if paper["general_instructions"]:
        lines.append("General Instructions:")
        for instruction in paper["general_instructions"]:
            _append_if_text(lines, instruction, "- ")
        lines.append("")

    for section in paper["sections"]:
        _append_if_text(lines, section["title"])
        section_meta = " | ".join(
            item
            for item in [
                section.get("type") and f"Type: {section['type']}",
                section.get("marks_distribution") and f"Marks: {section['marks_distribution']}",
            ]
            if item
        )
        _append_if_text(lines, section_meta)
        _append_if_text(lines, section.get("instructions"), "Instructions: ")
        lines.append("")

        for question in section["questions"]:
            number = _stringify(question["question_number"])
            question_text = _stringify(question["question_text"])
            label = f"{number}. " if number else ""
            _append_if_text(lines, f"{label}{question_text}")

            q_meta = " | ".join(
                item
                for item in [
                    question.get("type") and question["type"],
                    question.get("marks") and f"Marks: {question['marks']}",
                ]
                if item
            )
            _append_if_text(lines, q_meta, "   ")

            for option in question["options"]:
                _append_if_text(lines, option, "   - ")

            _append_if_text(lines, question.get("answer"), "   Answer: ")
            lines.append("")

        lines.append("")

    _append_if_text(lines, paper["note"], "Note: ")
    return "\n".join(line.rstrip() for line in lines if line is not None).strip()


def get_generation_scope_error(n8n_response: Any) -> str:
    """Return a frontend-safe error when the model refuses to generate a paper."""
    paper = _normalize_question_paper(n8n_response)
    note = _stringify(paper.get("note")).lower()
    title = _stringify(paper.get("title")).lower()
    combined = " ".join(part for part in [title, note] if part).strip()

    refusal_markers = [
        "beyond my academic question paper generation scope",
        "beyond the academic question paper generation scope",
        "outside my academic question paper generation scope",
        "outside the scope",
        "out of scope",
        "cannot generate",
        "can't generate",
        "unethical",
        "not related to academics",
        "not related to academic",
        "not academic",
        "unsafe request",
    ]

    if any(marker in combined for marker in refusal_markers):
        return "This prompt is not related to safe academic question paper generation. Please enter a valid academic prompt."

    if not paper["sections"] and note and "question paper" not in note:
        return "This prompt is not related to safe academic question paper generation. Please enter a valid academic prompt."

    return ""


def _set_default_style(document: Document) -> None:
    normal_style = document.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)


def _add_meta_line(document: Document, label: str, value: str) -> None:
    text = _stringify(value)
    if not text:
        return
    paragraph = document.add_paragraph()
    paragraph.add_run(f"{label}: ").bold = True
    paragraph.add_run(text)


def _add_question_paper_to_doc(document: Document, data: Any, fallback_title: str) -> None:
    paper = _normalize_question_paper(data, fallback_title=fallback_title)
    
    if paper.get("header"):
        try:
            doc_section = document.sections[0]
            header = doc_section.header
            header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            header_para.text = paper["header"]
            header_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        except Exception:
            pass

    heading = document.add_heading(paper["title"], 0)
    heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    if paper.get("time"):
        _add_meta_line(document, "Duration", paper["time"])

    _add_meta_line(document, "Subject", paper["subject"])
    _add_meta_line(document, "Grade", paper["grade"])
    _add_meta_line(document, "Total Marks", paper["total_marks"])
    _add_meta_line(document, "Paper Type", paper["paper_type"])
    _add_meta_line(document, "Difficulty", paper["difficulty"])

    if paper["general_instructions"]:
        document.add_heading("General Instructions", level=1)
        for instruction in paper["general_instructions"]:
            document.add_paragraph(instruction, style="List Bullet")

    for section in paper["sections"]:
        document.add_heading(section["title"], level=1)
        _add_meta_line(document, "Type", section.get("type", ""))
        _add_meta_line(document, "Marks", section.get("marks_distribution", ""))
        _add_meta_line(document, "Instructions", section.get("instructions", ""))

        for question in section["questions"]:
            number = _stringify(question["question_number"])
            question_text = _stringify(question["question_text"])
            question_line = f"{number}. {question_text}" if number else question_text
            paragraph = document.add_paragraph()
            paragraph.add_run(question_line).bold = True

            _add_meta_line(document, "Question Type", question.get("type", ""))
            _add_meta_line(document, "Marks", question.get("marks", ""))

            for option in question["options"]:
                document.add_paragraph(option, style="List Bullet")

            answer = _stringify(question.get("answer"))
            if answer:
                answer_paragraph = document.add_paragraph()
                answer_paragraph.add_run("Answer: ").bold = True
                answer_paragraph.add_run(answer)

    if paper["note"]:
        document.add_heading("Note", level=1)
        document.add_paragraph(paper["note"])


def create_docx_from_n8n_response(
    n8n_response: Any,
    output_dir: str,
    filename: str,
    title: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    document = Document()
    _set_default_style(document)
    _add_question_paper_to_doc(document, n8n_response, title)
    document.save(output_path)
    return output_path
