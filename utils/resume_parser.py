"""
Resume Parser Module
Extracts text and structured information from PDF and DOCX resumes.
Uses PyPDF2, pdfplumber, and python-docx for parsing.
Uses spaCy and NLTK for NLP processing.
"""

import re
import io
from typing import Dict, List, Tuple, Optional

# PDF parsing
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# DOCX parsing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# NLP
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    SPACY_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
        nltk.download("stopwords", quiet=True)
        nltk.download("wordnet", quiet=True)
        nltk.download("averaged_perceptron_tagger", quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


# ─── COMPREHENSIVE SKILLS DICTIONARY ─────────────────────────────────────────

SKILLS_DB = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "r",
        "go", "rust", "swift", "kotlin", "scala", "ruby", "php", "perl",
        "bash", "shell", "powershell", "matlab", "julia"
    ],
    "web": [
        "html", "css", "react", "angular", "vue", "nextjs", "nodejs", "express",
        "django", "flask", "fastapi", "spring", "laravel", "rails", "asp.net",
        "graphql", "rest", "api", "tailwind", "bootstrap", "webpack", "vite"
    ],
    "data_science": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "keras", "pytorch", "scikit-learn", "pandas", "numpy",
        "matplotlib", "seaborn", "plotly", "jupyter", "data analysis",
        "statistical analysis", "regression", "classification", "clustering",
        "neural network", "cnn", "rnn", "lstm", "transformer", "bert", "gpt",
        "xgboost", "lightgbm", "random forest", "svm", "feature engineering"
    ],
    "databases": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "cassandra", "dynamodb", "elasticsearch", "firebase", "neo4j",
        "nosql", "database design", "query optimization"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "github actions", "terraform", "ansible", "linux", "nginx", "apache",
        "microservices", "serverless", "lambda", "ec2", "s3", "devops",
        "helm", "prometheus", "grafana", "elk stack"
    ],
    "tools": [
        "git", "github", "gitlab", "jira", "confluence", "postman", "swagger",
        "figma", "tableau", "power bi", "excel", "spark", "hadoop", "airflow",
        "kafka", "rabbitmq", "celery", "selenium", "pytest", "junit"
    ],
    "security": [
        "cybersecurity", "penetration testing", "ethical hacking", "network security",
        "encryption", "oauth", "jwt", "ssl", "firewalls", "ids/ips",
        "vulnerability assessment", "soc", "siem", "owasp"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "agile", "scrum", "kanban"
    ]
}

ALL_SKILLS = []
for category_skills in SKILLS_DB.values():
    ALL_SKILLS.extend(category_skills)
ALL_SKILLS = list(set(ALL_SKILLS))


# ─── TEXT EXTRACTION ─────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber (primary) or PyPDF2 (fallback)."""
    text = ""

    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass

    if not text and PYPDF2_AVAILABLE:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception:
            pass

    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception:
        return ""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Auto-detect file type and extract text."""
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    return ""


# ─── NLP PROCESSING ──────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s@.\-+]", " ", text)
    return text.strip().lower()


def tokenize_and_lemmatize(text: str) -> List[str]:
    """Tokenize and lemmatize text using NLTK."""
    if not NLTK_AVAILABLE:
        return text.lower().split()

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(t) for t in tokens
              if t.isalpha() and t not in stop_words and len(t) > 2]
    return tokens


# ─── INFORMATION EXTRACTION ──────────────────────────────────────────────────

import re

def extract_email(text):
    # This catches emails even if PDF extraction adds weird spacing
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text."""
    pattern = r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"
    match = re.search(pattern, text)
    return match.group().strip() if match else None


def extract_linkedin(text: str) -> Optional[str]:
    """Extract LinkedIn URL from text."""
    pattern = r"linkedin\.com/in/[\w\-]+"
    match = re.search(pattern, text, re.IGNORECASE)
    return f"https://{match.group()}" if match else None


def extract_github(text: str) -> Optional[str]:
    """Extract GitHub URL from text."""
    pattern = r"github\.com/[\w\-]+"
    match = re.search(pattern, text, re.IGNORECASE)
    return f"https://{match.group()}" if match else None


def extract_name(text: str) -> Optional[str]:
    """Extract candidate name from resume (first non-empty line heuristic + NER)."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first = lines[0]
        if len(first.split()) <= 5 and not any(c in first for c in ["@", "http", "+"]):
            return first.title()

    if SPACY_AVAILABLE:
        doc = nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.title()
    return None


def extract_skills(text: str) -> List[str]:
    """Extract skills by matching against the skills database."""
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(list(set(found)))


def extract_education(text: str) -> List[str]:
    """Extract education qualifications."""
    degrees = [
        "b.tech", "b.e", "btech", "bachelor", "b.sc", "bsc", "b.com",
        "m.tech", "mtech", "master", "m.sc", "msc", "mba", "phd", "ph.d",
        "diploma", "associate", "12th", "10th", "hsc", "ssc", "graduation"
    ]
    found = []
    text_lower = text.lower()
    for deg in degrees:
        if deg in text_lower:
            found.append(deg.upper())
    return list(set(found))


def extract_experience_years(text: str) -> Optional[float]:
    """Extract years of experience from resume text."""
    patterns = [
        r"(\d+\.?\d*)\+?\s*years?\s*of\s*experience",
        r"(\d+\.?\d*)\+?\s*years?\s*experience",
        r"experience\s*of\s*(\d+\.?\d*)\+?\s*years?",
    ]
    for pat in patterns:
        m = re.search(pat, text.lower())
        if m:
            return float(m.group(1))
    return None


def extract_certifications(text: str) -> List[str]:
    """Extract certifications from resume."""
    cert_keywords = [
        "aws certified", "google cloud", "azure certified", "pmp", "ceh",
        "cissp", "comptia", "ccna", "ccnp", "tensorflow certificate",
        "coursera", "udemy", "edx", "certification", "certified"
    ]
    found = []
    text_lower = text.lower()
    for cert in cert_keywords:
        if cert in text_lower:
            found.append(cert.title())
    return list(set(found))


# ─── FULL RESUME PARSER ───────────────────────────────────────────────────────

def parse_resume(file_bytes: bytes, filename: str) -> Dict:
    """
    Full resume parsing pipeline.
    Returns structured resume data dictionary.
    """
    raw_text = extract_text(file_bytes, filename)

    if not raw_text:
        return {"error": "Could not extract text from resume."}

    parsed = {
        "raw_text": raw_text,
        "name": extract_name(raw_text),
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
        "linkedin": extract_linkedin(raw_text),
        "github": extract_github(raw_text),
        "skills": extract_skills(raw_text),
        "education": extract_education(raw_text),
        "certifications": extract_certifications(raw_text),
        "experience_years": extract_experience_years(raw_text),
        "word_count": len(raw_text.split()),
        "char_count": len(raw_text),
    }

    return parsed
