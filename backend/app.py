import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import warnings
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

try:
    from backend.services.document_exporter import (
        build_preview_text,
        create_docx_from_n8n_response,
        get_generation_scope_error,
        normalize_question_paper,
        parse_n8n_body,
    )
    from backend.services.prompt_generator import build_payload
    from backend.services.prompt_guard import validate_generation_prompt
    from backend.services.file_processor import process_file
    from backend.services.syllabus_parser import parse_syllabus_content
except ImportError:
    from services.document_exporter import (
        build_preview_text,
        create_docx_from_n8n_response,
        get_generation_scope_error,
        normalize_question_paper,
        parse_n8n_body,
    )
    from services.prompt_generator import build_payload
    from services.prompt_guard import validate_generation_prompt
    from services.file_processor import process_file
    from services.syllabus_parser import parse_syllabus_content

warnings.filterwarnings("ignore")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
UPLOAD_DIR = DOWNLOADS_DIR
GENERATED_DIR = DOWNLOADS_DIR
MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE_BYTES
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook-test/generate-paper",
)


def _save_uploaded_file(uploaded_file):
    if not uploaded_file or not uploaded_file.filename:
        return "", ""

    original_name = secure_filename(uploaded_file.filename)
    _, extension = os.path.splitext(original_name)
    extension = extension.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return "", ""

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"{uuid4().hex}{extension}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)
    uploaded_file.save(saved_path)
    return saved_path, original_name


def _post_to_n8n(payload):
    request_body = json.dumps(payload).encode("utf-8")
    webhook_request = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(webhook_request, timeout=60) as response:
        raw_body = response.read().decode("utf-8")
        return {
            "status_code": response.getcode(),
            "body": parse_n8n_body(raw_body),
        }


def _build_download_filename(subject: str, grade: str, board: str, marks: str) -> str:
    parts = [subject, grade, board, f"{marks} Marks" if marks else ""]
    label = "_".join(part.strip().replace(" ", "_") for part in parts if str(part).strip())
    label = re.sub(r"[^A-Za-z0-9_-]+", "", label).strip("_")
    return f"{label or 'Generated_Question_Paper'}.docx"


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Backend running"})


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(_error):
    return jsonify(
        {
            "status": "error",
            "message": "Uploaded file is too large. Please upload a file up to 100 MB.",
            "error_code": "FILE_TOO_LARGE",
            "max_size_mb": 100,
        }
    ), 413


@app.route("/generated/<path:filename>", methods=["GET"])
def generated_file(filename):
    return send_from_directory(GENERATED_DIR, filename, as_attachment=False)


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    requested_name = request.args.get("name", "").strip()
    download_name = requested_name or filename
    if not download_name.lower().endswith(".docx"):
        download_name = f"{download_name}.docx"

    return send_from_directory(
        GENERATED_DIR,
        filename,
        as_attachment=True,
        download_name=download_name,
    )


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.form.to_dict() or request.get_json(silent=True) or {}
        uploaded_files = request.files.getlist("file")
        
        saved_file_paths = []
        original_filenames = []
        
        for uf in uploaded_files:
            sf, of = _save_uploaded_file(uf)
            if sf:
                saved_file_paths.append(sf)
                original_filenames.append(of)

        print("\n┌─── REQUEST ───────────────────────────────────────", flush=True)
        print(f"│  Content-Type : {request.content_type}", flush=True)
        print(f"│  Form Keys    : {', '.join(data.keys()) or '(none)'}", flush=True)
        if original_filenames:
            for of in original_filenames:
                print(f"│  File         : {of}", flush=True)
            print(f"│  Saved To     : {', '.join(saved_file_paths)}", flush=True)
        else:
            print("│  File         : (none)", flush=True)
        print("└──────────────────────────────────────────────────", flush=True)

        if saved_file_paths:
            data["file_paths"] = saved_file_paths
        if original_filenames:
            data["document_names"] = original_filenames

        # 1. Text Extraction and Page Counting
        combined_text = ""
        total_pdf_pages = 0
        if saved_file_paths:
            print("│  Status       : Extracting text from files...", flush=True)
            for sp in saved_file_paths:
                file_text = process_file(sp)
                if file_text:
                    combined_text += "\n" + file_text
                    
                if sp.lower().endswith(".pdf"):
                    try:
                        import pdfplumber
                        with pdfplumber.open(sp) as pdf:
                            total_pdf_pages += len(pdf.pages)
                    except Exception as ext:
                        print(f"│  Error        : PDF page count failed ({ext})", flush=True)

        # 2. Syllabus Parsing (JSON Format)
        syllabus_validation = {}
        if combined_text.strip():
            print("│  Status       : Parsing syllabus content...", flush=True)
            syllabus_validation = parse_syllabus_content(combined_text, total_pages=total_pdf_pages)
            
            if not syllabus_validation.get("is_valid", False):
                print(f"│  Error        : Invalid syllabus ({syllabus_validation.get('reason')})", flush=True)
                return jsonify({
                    "status": "error",
                    "message": syllabus_validation.get("reason", "Uploaded document is not a valid syllabus."),
                    "error_code": "INVALID_SYLLABUS",
                }), 422
            
            data["syllabus_metadata"] = syllabus_validation.get("extracted_data", {})

        # 3. Subject Mismatch Validation
        if data.get("syllabus_metadata"):
            user_subject = str(data.get("subject", "")).strip()
            parsed_subject = str(data["syllabus_metadata"].get("subject", "")).strip()
            
            if user_subject:
                print(f"│  Validation   : Comparing user subject '{user_subject}' with parsed subject '{parsed_subject}'", flush=True)
                
                common_stopwords = {"and", "of", "the", "in", "to", "for", "course", "subject", "code", "name", "title", "lab", "systems", "engineering", "introduction", "advanced", "basic", "basics", "applied", "principles", "fundamentals", "theory", "part"}
                
                user_w = set(re.findall(r'\b\w+\b', user_subject.lower())) - common_stopwords
                parsed_w = set(re.findall(r'\b\w+\b', parsed_subject.lower())) - common_stopwords
                
                is_substring = user_subject.lower() in parsed_subject.lower() or parsed_subject.lower() in user_subject.lower()
                has_intersection = bool(parsed_w.intersection(user_w))
                
                is_acronym_match = False
                if len(user_subject) <= 5 and user_subject.isalpha():
                    doc_head_words = [w for w in re.findall(r'\b[a-zA-Z]+\b', parsed_subject.lower()) if w not in common_stopwords]
                    doc_initials = "".join([w[0] for w in doc_head_words])
                    if user_subject.lower() in doc_initials:
                        is_acronym_match = True

                if not (has_intersection or is_substring or is_acronym_match):
                    exact_pattern = r'\b' + re.escape(user_subject.lower()) + r'\b'
                    is_in_text = bool(re.search(exact_pattern, combined_text.lower()))
                    if not is_in_text:
                        print(f"│  Error        : Subject mismatch. User: {user_subject}, Doc: {parsed_subject}", flush=True)
                        return jsonify({
                            "status": "error",
                            "message": "Entered subject is a mismatch you please check again",
                            "error_code": "SUBJECT_MISMATCH",
                        }), 422

        # 4. Custom Prompt Checking (Academic Only)
        print("│  Status       : Checking academic relevance of custom prompt...", flush=True)
        is_valid_prompt, prompt_error = validate_generation_prompt(
            data.get("prompt", data.get("custom_prompt", "")),
            data.get("subject", ""),
        )
        if not is_valid_prompt:
            print(f"│  Error        : {prompt_error}", flush=True)
            return jsonify({
                "status": "error",
                "message": prompt_error,
                "error_code": "INVALID_PROMPT",
            }), 422

        payload, debug = build_payload(data)
        
        print("\n=== DEBUG: PAYLOAD CONTENT ===")
        print(json.dumps({k: v[:50] if isinstance(v, str) else v for k, v in payload.items()}, indent=2))
        print("==============================\n", flush=True)

        with open("last_debug_output.json", "w") as f:
            import copy
            debug_safe = copy.deepcopy(debug)
            if "source_document" in debug_safe:
                debug_safe["source_document"]["text"] = str(debug_safe["source_document"].get("text", ""))[:100] + "..."
                debug_safe["source_document"]["context"] = str(debug_safe["source_document"].get("context", ""))[:100] + "..."
            json.dump({"payload": payload, "debug": debug_safe, "file_paths": saved_file_paths}, f, indent=2)

        source_document = debug.get("source_document", {})
        n8n_result = _post_to_n8n(payload)
        n8n_body = n8n_result.get("body", {})
        scope_error = get_generation_scope_error(n8n_body)

        if scope_error:
            return jsonify(
                {
                    "status": "error",
                    "message": scope_error,
                    "error_code": "OUT_OF_SCOPE_PROMPT",
                    "n8n_response": n8n_body,
                }
            ), 422

        # Final check: Is this a valid paper?
        from services.document_exporter import _is_question_paper_payload, _extract_nested_payload
        extracted_payload = _extract_nested_payload(n8n_body)
        if not _is_question_paper_payload(extracted_payload):
            print("│  Error        : AI generation failed or returned invalid data.", flush=True)
            print(f"│  Response     : {json.dumps(n8n_body)[:200]}...", flush=True)
            return jsonify({
                "status": "error",
                "message": "Internal server error occurred",
                "error_code": "GENERATION_FAILED",
                "n8n_response": n8n_body
            }), 500

        preview_text = build_preview_text(n8n_body)
        preview_paper = normalize_question_paper(
            n8n_body,
            fallback_title=payload.get("title", "Generated Question Paper"),
        )
        generated_filename = f"{uuid4().hex}.docx"
        download_filename = _build_download_filename(
            payload.get("subject", ""),
            payload.get("grade", ""),
            payload.get("board", ""),
            str(payload.get("marks", payload.get("total_marks", ""))),
        )
        docx_path = create_docx_from_n8n_response(
            n8n_response=n8n_body,
            output_dir=GENERATED_DIR,
            filename=generated_filename,
            title=payload.get("title", "Generated Question Paper"),
        )
        docx_url = f"/generated/{os.path.basename(docx_path)}"
        download_url = f"/download/{os.path.basename(docx_path)}?name={urllib.parse.quote(download_filename)}"

        print("\n┌─── PAYLOAD ───────────────────────────────────────", flush=True)
        print(json.dumps(payload, indent=2, default=str), flush=True)
        print("└──────────────────────────────────────────────────", flush=True)

        src_type = source_document.get("file_type", "") or "(none)"
        src_text_len = len(source_document.get("text", ""))
        src_chunks = len(source_document.get("chunks", []))
        src_selected = len(source_document.get("selected_chunks", []))

        print("\n┌─── SOURCE DOCUMENT ───────────────────────────────", flush=True)
        print(f"│  Type             : {src_type}", flush=True)
        print(f"│  Extracted Text   : {src_text_len} chars", flush=True)
        print(f"│  Total Chunks     : {src_chunks}", flush=True)
        print(f"│  Selected Chunks  : {src_selected}", flush=True)
        print("└──────────────────────────────────────────────────", flush=True)

        print("\n┌─── N8N RESULT ────────────────────────────────────", flush=True)
        print(f"│  Status Code   : {n8n_result.get('status_code')}", flush=True)
        print(f"│  Preview       : {len(preview_text)} chars", flush=True)
        print(f"│  DOCX URL      : {docx_url}", flush=True)
        print("└──────────────────────────────────────────────────", flush=True)

        return jsonify(
            {
                "status": "success",
                "prompt": payload,
                "source_document": source_document,
                "retrieval_topic": debug.get("retrieval_topic", ""),
                "sections": debug.get("sections", []),
                "n8n_webhook_url": N8N_WEBHOOK_URL,
                "n8n_response": n8n_body,
                "preview_text": preview_text,
                "preview_paper": preview_paper,
                "docx_url": docx_url,
                "docx_download_url": download_url,
                "docx_filename": generated_filename,
                "docx_download_name": download_filename,
            }
        )
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = ""

        print("\n┌─── N8N HTTP ERROR ────────────────────────────────", flush=True)
        print(f"│  Status Code  : {e.code}", flush=True)
        print(f"│  Webhook URL  : {N8N_WEBHOOK_URL}", flush=True)
        print(f"│  Body         : {error_body[:300]}", flush=True)
        print("└──────────────────────────────────────────────────", flush=True)
        return jsonify(
            {
                "status": "error",
                "message": f"n8n webhook returned HTTP {e.code}",
                "n8n_webhook_url": N8N_WEBHOOK_URL,
                "n8n_error_body": error_body,
            }
        ), 502
    except urllib.error.URLError as e:
        print("\n┌─── N8N URL ERROR ─────────────────────────────────", flush=True)
        print(f"│  Webhook URL  : {N8N_WEBHOOK_URL}", flush=True)
        print(f"│  Reason       : {e.reason}", flush=True)
        print("└──────────────────────────────────────────────────", flush=True)
        return jsonify(
            {
                "status": "error",
                "message": f"Unable to reach n8n webhook: {e.reason}",
                "n8n_webhook_url": N8N_WEBHOOK_URL,
            }
        ), 502
    except Exception as e:
        print(f"\n┌─── ERROR ─────────────────────────────────────────", flush=True)
        print(f"│  {e}", flush=True)
        print(f"└──────────────────────────────────────────────────", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    import click

    click.echo = lambda *args, **kwargs: None
    app.run(debug=True, use_reloader=False)
