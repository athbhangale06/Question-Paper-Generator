import os
import re
from collections import Counter
from typing import Dict, List

import pdfplumber

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

try:
    from backend.services.docx_compat import Document
except ImportError:
    from services.docx_compat import Document


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _clean_text(text: str) -> str:
    """Normalize extracted text so downstream chunking is stable."""
    if not text:
        return ""

    # Replace control characters (except Tab, CR, LF) with space to prevent downstream DOCX generation errors
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _looks_like_scanned_text(text: str) -> bool:
    normalized = _clean_text(text)
    if not normalized:
        return True
    alpha_chars = sum(1 for char in normalized if char.isalpha())
    return len(normalized) < 120 or alpha_chars < 40


def _ocr_image(image) -> str:
    if pytesseract is None or image is None:
        return ""

    try:
        ocr_text = pytesseract.image_to_string(image)
    except Exception as exc:
        print(f"OCR image extraction error: {exc}", flush=True)
        return ""

    return _clean_text(ocr_text)


def extract_text_from_image(file_path: str) -> str:
    if not file_path or not os.path.exists(file_path) or Image is None:
        return ""

    try:
        with Image.open(file_path) as image:
            return _ocr_image(image)
    except Exception as exc:
        print(f"Image extraction error: {exc}", flush=True)
        return ""


def _ocr_pdf_pages(file_path: str) -> str:
    if pdfium is None or pytesseract is None or Image is None:
        return ""

    page_texts: List[str] = []

    try:
        pdf = pdfium.PdfDocument(file_path)
        for index in range(len(pdf)):
            page = pdf[index]
            bitmap = page.render(scale=2)
            pil_image = bitmap.to_pil()
            page_text = _ocr_image(pil_image)
            if page_text:
                page_texts.append(page_text)
    except Exception as exc:
        print(f"PDF OCR extraction error: {exc}", flush=True)
        return ""

    return "\n\n".join(page_texts).strip()


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDFs, with OCR fallback for scanned pages."""
    if not file_path or not os.path.exists(file_path):
        return ""

    page_texts: List[str] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                return ""

            for page in pdf.pages:
                raw_text = page.extract_text() if page else ""
                cleaned_page = _clean_text(raw_text or "")
                if cleaned_page:
                    page_texts.append(cleaned_page)
    except Exception as exc:
        print(f"PDF extraction error: {exc}", flush=True)
        return ""

    extracted_text = "\n\n".join(page_texts).strip()
    if _looks_like_scanned_text(extracted_text):
        ocr_text = _ocr_pdf_pages(file_path)
        if ocr_text:
            return ocr_text

    return extracted_text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX files to preserve existing project support."""
    if not file_path or not os.path.exists(file_path):
        return ""

    paragraphs: List[str] = []

    try:
        document = Document(file_path)
        for paragraph in document.paragraphs:
            cleaned_paragraph = _clean_text(paragraph.text)
            if cleaned_paragraph:
                paragraphs.append(cleaned_paragraph)
    except Exception as exc:
        print(f"DOCX extraction error: {exc}", flush=True)
        return ""

    return "\n\n".join(paragraphs).strip()


def chunk_text(text: str, chunk_size: int = 1200) -> List[str]:
    """Split text into readable chunks near the requested character size."""
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return []

    paragraphs = [part.strip() for part in cleaned_text.split("\n\n") if part.strip()]
    if not paragraphs:
        return []

    chunks: List[str] = []
    current_chunk = ""
    max_chunk_size = max(chunk_size, 900)

    for paragraph in paragraphs:
        if len(paragraph) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            start = 0
            paragraph_length = len(paragraph)
            while start < paragraph_length:
                end = min(start + max_chunk_size, paragraph_length)
                if end < paragraph_length:
                    split_at = paragraph.rfind(" ", start, end)
                    if split_at > start:
                        end = split_at

                piece = paragraph[start:end].strip()
                if piece:
                    chunks.append(piece)
                start = end + 1 if end < paragraph_length and paragraph[end:end + 1] == " " else end
            continue

        separator = "\n\n" if current_chunk else ""
        candidate = f"{current_chunk}{separator}{paragraph}" if current_chunk else paragraph

        if len(candidate) <= max_chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _tokenize_query(query: str) -> List[str]:
    return re.findall(r"\b\w+\b", (query or "").lower())


def find_relevant_chunks(chunks: List[str], query: str, top_k: int = 3) -> List[str]:
    """Return the most relevant chunks for a topic, with a safe fallback."""
    if not chunks:
        return []

    normalized_query = (query or "").strip().lower()
    query_tokens = _tokenize_query(normalized_query)

    if not normalized_query:
        return chunks[: max(1, min(top_k, len(chunks)))]

    ranked_chunks = []
    for index, chunk in enumerate(chunks):
        lowered_chunk = chunk.lower()
        chunk_tokens = Counter(re.findall(r"\b\w+\b", lowered_chunk))

        score = 0
        if normalized_query in lowered_chunk:
            score += 5

        for token in query_tokens:
            score += chunk_tokens.get(token, 0)

        if score > 0:
            ranked_chunks.append((score, index, chunk))

    if not ranked_chunks:
        return chunks[:1]

    ranked_chunks.sort(key=lambda item: (-item[0], item[1]))
    limit = max(1, min(top_k, 3, len(ranked_chunks)))
    return [chunk for _, _, chunk in ranked_chunks[:limit]]


def compress_chunk_text(text: str, max_sentences: int = 4) -> str:
    """Reduce chunk size by dropping duplicates and keeping the densest sentences."""
    cleaned = _clean_text(text)
    if not cleaned:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    normalized_seen = set()
    unique_sentences: List[str] = []

    for sentence in sentences:
        normalized = re.sub(r"\W+", " ", sentence.lower()).strip()
        if not normalized or normalized in normalized_seen:
            continue
        normalized_seen.add(normalized)
        unique_sentences.append(sentence.strip())

    if len(unique_sentences) <= max_sentences:
        return " ".join(unique_sentences).strip()

    scored_sentences = []
    for index, sentence in enumerate(unique_sentences):
        words = re.findall(r"\b\w+\b", sentence.lower())
        unique_word_count = len(set(words))
        digit_bonus = 2 if re.search(r"\d", sentence) else 0
        keyword_bonus = 2 if re.search(r"\b(question|answer|chapter|unit|topic|definition|formula|theorem)\b", sentence.lower()) else 0
        score = unique_word_count + digit_bonus + keyword_bonus
        scored_sentences.append((score, index, sentence))

    scored_sentences.sort(key=lambda item: (-item[0], item[1]))
    selected = sorted(scored_sentences[:max_sentences], key=lambda item: item[1])
    return " ".join(sentence for _, _, sentence in selected).strip()


def summarize_chunks(chunks: List[str], query: str, max_chunks: int = 3) -> List[str]:
    """Create low-token extractive summaries for the most relevant chunks."""
    relevant_chunks = find_relevant_chunks(chunks, query, top_k=max_chunks)
    summaries: List[str] = []

    for chunk in relevant_chunks:
        compressed = compress_chunk_text(chunk, max_sentences=4)
        if compressed:
            summaries.append(compressed)

    return summaries


def process_pdf_for_ai(file_path: str, topic: str) -> str:
    """Build an AI-ready context string from a PDF and topic."""
    extracted_text = extract_text_from_pdf(file_path)
    if not extracted_text:
        return ""

    chunks = chunk_text(extracted_text)
    if not chunks:
        return extracted_text[:1200].strip()

    summarized_chunks = summarize_chunks(chunks, topic, max_chunks=3)
    return "\n\n".join(summarized_chunks).strip()


def process_document_for_ai(file_path: str, topic: str, chunk_size: int = 1200) -> Dict[str, object]:
    """Extract, OCR, chunk, compress, and summarize a supported document."""
    empty_result = {
        "file_path": file_path or "",
        "file_type": "",
        "text": "",
        "chunks": [],
        "compressed_chunks": [],
        "selected_chunks": [],
        "summaries": [],
        "context": "",
        "ocr_used": False,
    }

    if not file_path or not os.path.exists(file_path):
        return empty_result

    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(file_path)
    elif extension == ".docx":
        extracted_text = extract_text_from_docx(file_path)
    elif extension in IMAGE_EXTENSIONS:
        extracted_text = extract_text_from_image(file_path)
    else:
        extracted_text = ""

    chunks = chunk_text(extracted_text, chunk_size=chunk_size) if extracted_text else []
    compressed_chunks = [compress_chunk_text(chunk, max_sentences=5) for chunk in chunks]
    compressed_chunks = [chunk for chunk in compressed_chunks if chunk]
    selected_chunks = find_relevant_chunks(compressed_chunks or chunks, topic, top_k=3) if chunks else []
    summaries = summarize_chunks(chunks, topic, max_chunks=3) if chunks else []
    context_parts = summaries or selected_chunks
    context = "\n\n".join(part for part in context_parts if part).strip()
    ocr_used = extension in IMAGE_EXTENSIONS or (extension == ".pdf" and _looks_like_scanned_text(_clean_text(extracted_text[:200])))

    return {
        "file_path": file_path,
        "file_type": extension.lstrip("."),
        "text": extracted_text,
        "chunks": chunks,
        "compressed_chunks": compressed_chunks,
        "selected_chunks": selected_chunks,
        "summaries": summaries,
        "context": context,
        "ocr_used": ocr_used,
    }


def process_file(file_path: str) -> str:
    """Process supported files while keeping the existing public helper."""
    if not file_path:
        return ""

    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == ".pdf":
        print("Processing PDF file...", flush=True)
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        print("Processing DOCX file...", flush=True)
        return extract_text_from_docx(file_path)

    if extension in IMAGE_EXTENSIONS:
        print("Processing image file...", flush=True)
        return extract_text_from_image(file_path)

    print("Unsupported file type", flush=True)
    return ""
