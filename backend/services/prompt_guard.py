import re
from typing import Tuple


ACADEMIC_PATTERN = re.compile(
    r"\b("
    r"question\s*paper|exam|test|quiz|worksheet|assignment|assessment|"
    r"chapter|unit|lesson|topic|syllabus|curriculum|module|"
    r"mcq|multiple\s*choice|short\s*answer|long\s*answer|numerical|derivation|explanation|definition|"
    r"physics|chemistry|biology|science|mathematics|math|algebra|geometry|calculus|trigonometry|"
    r"history|geography|english|grammar|literature|computer|programming|coding|software|hardware|"
    r"economics|accountancy|commerce|civics|political\s*science|sociology|psychology|"
    r"engineering|mechanics|electronics|electrical|civil|chemical|"
    r"medicine|anatomy|physiology|pharmacology"
    r")\b",
    re.IGNORECASE,
)

PAPER_STRUCTURE_PATTERN = re.compile(
    r"\b("
    r"q\d+[a-z]?|question\s*\d+|main\s*question|sub\s*question|"
    r"section|part|marks?|format|pattern|template|"
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
    r"joke|story|poem|lyrics|song|roast|meme|recipe|cook|food|restaurant|chef|"
    r"weather|news|movie|cinema|actor|celebrity|instagram|tiktok|facebook|social\s*media|"
    r"love advice|relationship|date|travel|vacation|hotel|price|buy|shopping|"
    r"chatgpt|openai|gemini|claude|bot|ai\s*assistant"
    r")\b",
    re.IGNORECASE,
)


def validate_generation_prompt(prompt: str, subject: str = "") -> Tuple[bool, str]:
    prompt = str(prompt or "").strip()
    if not prompt:
        return False, "Please enter a clear academic prompt before generating."

    subject = str(subject or "").strip()
    
    # 1. Check for unsafe content first
    if UNSAFE_PATTERN.search(prompt):
        return False, "This prompt contains inappropriate content and cannot be processed for academic purposes."

    # 2. Check for unrelated/conversational content
    # If it looks like a general chatbot interaction and lacks academic context
    has_academic_context = bool(ACADEMIC_PATTERN.search(prompt) or 
                                ACADEMIC_PATTERN.search(subject) or 
                                PAPER_STRUCTURE_PATTERN.search(prompt))
                                
    if UNRELATED_PATTERN.search(prompt) and not has_academic_context:
        return False, "This prompt is not related to academic question paper generation. Please enter a valid academic prompt."

    # 3. Final strict check: It MUST have some academic or paper-structure context
    if not has_academic_context:
        return False, "Your prompt does not seem related to academic content. Please specify topics, chapters, or question paper requirements."

    return True, ""
