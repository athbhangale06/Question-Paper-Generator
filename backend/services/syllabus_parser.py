import re
from typing import Dict, Any

# Increased weights for highly specific syllabus terms
STRONG_POSITIVE_KEYWORDS = [
    "syllabus", "course outcome", "course outcomes", "course objective", 
    "course objectives", "subject code", "teaching scheme", "examination scheme", 
    "course content", "learning objectives", "learning outcomes", "course outline"
]

# Lower weights for general terms that can appear in textbooks too
WEAK_POSITIVE_KEYWORDS = [
    "module", "credits", "detailed content", "curriculum", "unit", "topics", "hours",
    "prerequisites"
]

# Highly indicative of a textbook or publication
STRONG_NEGATIVE_KEYWORDS = [
    "isbn", "all rights reserved", "publisher", "foreword", "preface", "acknowledgments",
    "copyright"
]

# Moderately indicative
WEAK_NEGATIVE_KEYWORDS = [
    "chapter", "exercise", "bibliography", "index", "edition", "references"
]

def parse_syllabus_content(text: str, total_pages: int = 0) -> Dict[str, Any]:
    """
    Parses the text of an uploaded document to determine if it is a valid syllabus.
    If valid, extracts key syllabus elements like nested Units, Course Outcomes (COs), and Subjects.
    """
    if not text or not text.strip():
        return {
            "is_valid": False, 
            "reason": "Empty document. Please upload a valid syllabus PDF."
        }
        
    text_lower = text.lower()
    
    # 1. Validation Heuristics using Scoring
    score = 0
    
    # Strong positive signals (+3)
    for word in STRONG_POSITIVE_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            score += 3
            
    # Weak positive signals (+1)
    for word in WEAK_POSITIVE_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            score += 1

    # Specific check for CO indicators like CO1, CO2, etc (+2)
    if re.search(r'\b(?:co1|co2|co3|co4|co5)\b', text_lower):
        score += 2
            
    # Strong negative signals (-3)
    for word in STRONG_NEGATIVE_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            score -= 3
            
    # Weak negative signals (-2)
    for word in WEAK_NEGATIVE_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            score -= 2
            
    # Soft heuristics for page count
    if total_pages > 0:
        if total_pages <= 10:
            score += 2  # Syllabuses are usually quite short
        elif total_pages <= 30:
            score += 1
        if total_pages > 50:
            score -= 3  # Unlikely to be just a syllabus text
        if total_pages > 120:
            score -= 5
    else:
        # fallback heuristic if total_pages not provided (e.g. pasted text)
        text_length = len(text)
        if text_length < 20000: # ~10 pages
            score += 2
        if text_length > 100000: # Approx 50+ pages
            score -= 3
        if text_length > 200000: # Approx 100+ pages
            score -= 5

    # Threshold for validation
    if score < 4:
        return {
            "is_valid": False, 
            "reason": f"Document does not match syllabus structure (Score {score} is too low). It may be a textbook or reference material."
        }
        
    # 2. Extraction Heuristics
    lines = text.split('\n')
    extracted = {
        "subject": "",
        "course_outcomes": [],
        "units": [],
        "topics": [] # Flat list mainly for backwards compatibility in prompt generator
    }
    
    # Try to extract subject
    subject_match = re.search(r'(?:subject|course)(?:\s*(?:name|title))?\s*[:\-]?\s*([A-Za-z0-9\s\&\-]+)', text, re.IGNORECASE)
    if subject_match:
        extracted["subject"] = subject_match.group(1).strip().split('\n')[0][:100]
        
    # Extract Course Outcomes (COs)
    capture_co = False
    for line in lines:
        lower_line = line.lower()
        if "course outcome" in lower_line or re.match(r"(?i)^co\d", line.strip()):
            capture_co = True
            
            # If the current line has the outcome on it, e.g. "CO1: Understand basic..."
            clean_line = re.sub(r'^(?:course outcomes?|co\d+)\s*[:\-]?\s*', '', line, flags=re.IGNORECASE).strip()
            if len(clean_line) > 5:
                extracted["course_outcomes"].append(clean_line)
            continue
            
        if capture_co:
            # Stop if we hit another major heading
            if re.match(r'(?i)^(module|unit|detailed content|evaluation|hours|credits)', line.strip()):
                capture_co = False
                continue
                
            stripped = line.strip()
            if stripped:
                clean_line = re.sub(r'^(?:[0-9]+[\.\:]|[-•])\s*', '', stripped).strip()
                if len(clean_line) > 5:
                    extracted["course_outcomes"].append(clean_line)
            else:
                pass # blank lines can be ignored, but shouldn't necessarily end the block
                
    # Extract Units / Modules
    current_unit = None
    capture_unit_content = False
    
    for line in lines:
        lower_line = line.lower()
        
        # New unit starts
        # Match "Module 1", "Unit I", etc.
        unit_match = re.match(r'(?i)^(?:module|unit)\s*[0-9A-Za-z]+(.*)', line.strip())
        if unit_match:
            if current_unit:
                extracted["units"].append(current_unit)
                
            unit_title = line.strip()
            current_unit = {
                "name": unit_title,
                "topics": []
            }
            capture_unit_content = True
            continue
            
        if capture_unit_content and current_unit:
            # Stop unit capture if we see reference materials
            if re.match(r'(?i)^(reference|textbooks|suggested reading)', line.strip()):
                capture_unit_content = False
                continue
                
            # If it's a topic item (bullet or text block)
            clean_topic = re.sub(r'^[-•\.\*]\s*|^[0-9]+\.[0-9]+\s*', '', line).strip()
            if 5 < len(clean_topic) < 150:
                current_unit["topics"].append(clean_topic)
                extracted["topics"].append(clean_topic)
                
    if current_unit and current_unit not in extracted["units"]:
        extracted["units"].append(current_unit)
                    
    # Clean and Deduplicate
    extracted["course_outcomes"] = list(dict.fromkeys(extracted["course_outcomes"]))[:10]
    extracted["topics"] = list(dict.fromkeys(extracted["topics"]))[:20]
    
    # Create a consolidated text representation for the AI payload
    content_parts = []
    if extracted["subject"]:
        content_parts.append(f"Subject: {extracted['subject']}")
    
    if extracted["course_outcomes"]:
        content_parts.append("\nCourse Outcomes:")
        content_parts.extend([f"- {co}" for co in extracted["course_outcomes"]])
        
    if extracted["units"]:
        content_parts.append("\nDetailed Syllabus Units:")
        for unit in extracted["units"]:
            content_parts.append(f"Module/Unit: {unit['name']}")
            if unit.get("topics"):
                content_parts.extend([f"  • {t}" for t in unit["topics"]])
                
    extracted["fileContent"] = "\n".join(content_parts).strip()
    
    return {
        "is_valid": True,
        "extracted_data": extracted
    }
