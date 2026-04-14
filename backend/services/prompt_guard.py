import re
from typing import Tuple


ACADEMIC_PATTERN = re.compile(
    r"\b("
    r"question\s*paper|exam|test|quiz|worksheet|assignment|assessment|"
    r"chapter|unit|lesson|topic|syllabus|curriculum|"
    r"mcq|multiple\s*choice|short\s*answer|long\s*answer|numerical|derivation|"
    r"physics|chemistry|biology|science|mathematics|math|algebra|geometry|"
    r"history|geography|english|grammar|literature|computer|programming|"
    r"economics|accountancy|commerce|civics|political\s*science"
    r")\b",
    re.IGNORECASE,
)

PAPER_STRUCTURE_PATTERN = re.compile(
    r"\b("
    r"q\d+[a-z]?|question\s*\d+|main\s*question|sub\s*question|"
    r"section|part|marks?|format|pattern|"
    r"q1|q2|q3|q4|q5|q6|q7|q8|q9|q10"
    r")\b",
    re.IGNORECASE,
)

UNSAFE_PATTERN = re.compile(
    r"\b("
    r"sex|sexual|porn|nude|adult|escort|fetish|"
    r"kill|murder|bomb|weapon|terror|attack|suicide|self[- ]?harm|"
    r"hack|hacking|phish|phishing|malware|ransomware|"
    r"drugs?|cocaine|heroin|meth|fraud|scam|forgery|counterfeit|"
    r"hate|abuse|harass|harassment|girlfriend|boyfriend|dating|flirt|romance"
    r")\b",
    re.IGNORECASE,
)

UNRELATED_PATTERN = re.compile(
    r"\b("
    r"hello|hi|hey|how are you|who are you|what are you|"
    r"joke|story|poem|lyrics|song|roast|meme|recipe|cook|food|"
    r"weather|news|movie|instagram|love advice|relationship|"
    r"chatgpt|openai|gemini"
    r")\b",
    re.IGNORECASE,
)


def validate_generation_prompt(prompt: str, subject: str = "") -> Tuple[bool, str]:
    prompt = str(prompt or "").strip()
    subject = str(subject or "").strip()
    combined = " ".join(part for part in [subject, prompt] if part).strip()

    if not prompt:
        return False, "Please enter a clear academic prompt before generating."

    if UNSAFE_PATTERN.search(prompt):
        return False, "This prompt is outside safe academic question paper generation. Please enter a valid academic prompt."

    has_academic_context = bool(ACADEMIC_PATTERN.search(combined) or PAPER_STRUCTURE_PATTERN.search(prompt))

    if UNRELATED_PATTERN.search(prompt) and not has_academic_context:
        return False, "This prompt is not related to academic question paper generation. Please enter a valid academic prompt."

    if not has_academic_context:
        return False, "Please enter an academic prompt related to a subject, topic, chapter, exam, or question paper."

    return True, ""
