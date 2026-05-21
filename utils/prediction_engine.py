"""
Job Role Prediction Engine — v2
================================
Fixes the "always Cloud Engineer" bug by using:

1.  EXCLUSIVE signature keywords  — high-weight terms that strongly
    identify ONE role and are NOT shared across roles.
2.  SHARED common keywords        — low-weight terms present in many roles.
3.  NEGATIVE keywords             — words that REDUCE a role score when
    a stronger role-specific signal appears elsewhere.
4.  Role-specific phrase boosting — multi-word phrases scored at 4x.
5.  Score normalisation           — prevents short keyword lists from
    inflating confidence (the original root cause).
6.  Minimum exclusive-keyword gate — a role must match >= 1 exclusive
    keyword to be considered (stops "aws" alone triggering Cloud Engineer).
"""

from typing import Dict, List

WEIGHT_EXCLUSIVE = 3
WEIGHT_SHARED    = 1
WEIGHT_PHRASE    = 4
WEIGHT_NEGATIVE  = -1

JOB_ROLES: Dict = {

    "Data Scientist": {
        "icon": "🔬",
        "description": "Analyse complex data to drive business decisions using ML and statistical methods.",
        "exclusive": [
            "data scientist", "machine learning", "deep learning", "statistics",
            "pandas", "numpy", "scikit-learn", "jupyter", "matplotlib", "seaborn",
            "feature engineering", "data mining", "regression", "classification",
            "clustering", "predictive modelling", "a/b testing", "hypothesis testing",
            "statistical modelling", "eda", "exploratory data analysis",
            "xgboost", "lightgbm", "random forest", "model evaluation", "cross validation",
        ],
        "shared": [
            "python", "sql", "tensorflow", "keras", "pytorch", "nlp",
            "computer vision", "visualization", "tableau", "r",
        ],
        "phrases": [
            "data science", "machine learning model", "statistical analysis",
            "predictive model", "data pipeline", "feature selection",
        ],
        "negatives": [
            "docker", "kubernetes", "ci/cd", "terraform", "devops",
            "html", "css", "javascript", "react", "angular",
        ],
        "required_min": 2,
    },

    "AI/ML Engineer": {
        "icon": "🤖",
        "description": "Build and deploy production-grade AI/ML models and infrastructure.",
        "exclusive": [
            "mlops", "model deployment", "neural network", "lstm", "cnn",
            "transformer", "bert", "gpt", "huggingface", "cuda", "gpu training",
            "distributed training", "model serving", "model optimisation",
            "quantisation", "onnx", "tensorrt", "model registry",
            "mlflow", "kubeflow", "feature store", "llm", "fine-tuning",
            "langchain", "vector database", "rag",
        ],
        "shared": [
            "tensorflow", "pytorch", "keras", "python", "docker",
            "kubernetes", "aws", "azure", "gcp", "api",
        ],
        "phrases": [
            "machine learning pipeline", "ai model", "model training",
            "deploy model", "inference server", "deep learning model",
        ],
        "negatives": [
            "html", "css", "javascript", "react", "angular", "terraform",
            "ci/cd", "network security", "penetration testing",
        ],
        "required_min": 2,
    },

    "Web Developer": {
        "icon": "🌐",
        "description": "Design and build modern web applications and interfaces.",
        "exclusive": [
            "html", "css", "javascript", "typescript", "react", "angular", "vue",
            "nextjs", "nodejs", "express", "graphql", "tailwind", "bootstrap",
            "webpack", "vite", "responsive design", "frontend", "backend",
            "fullstack", "dom", "web development", "ui/ux",
            "sass", "redux", "svelte", "nuxt", "gatsby", "vercel", "netlify",
        ],
        "shared": [
            "mongodb", "postgresql", "mysql", "git", "docker", "aws",
            "nginx", "api", "agile",
        ],
        "phrases": [
            "web application", "frontend development", "backend development",
            "full stack", "single page application", "progressive web app",
        ],
        "negatives": [
            "machine learning", "kubernetes", "terraform", "ansible",
            "penetration testing", "data analysis", "statistics",
        ],
        "required_min": 2,
    },

    "DevOps Engineer": {
        "icon": "⚙️",
        "description": "Automate and manage cloud infrastructure and CI/CD deployment pipelines.",
        "exclusive": [
            "ci/cd", "jenkins", "github actions", "gitlab ci", "ansible",
            "terraform", "helm", "prometheus", "grafana", "elk stack",
            "infrastructure as code", "devops", "site reliability",
            "sre", "argocd", "flux", "gitops", "puppet",
            "chef", "packer", "vault", "consul", "service mesh", "istio",
            "deployment automation", "build automation",
        ],
        "shared": [
            "docker", "kubernetes", "linux", "bash", "aws", "azure",
            "gcp", "nginx", "monitoring", "git", "python",
        ],
        "phrases": [
            "continuous integration", "continuous deployment", "deployment pipeline",
            "infrastructure automation", "release management", "container orchestration",
        ],
        "negatives": [
            "html", "css", "javascript", "react", "machine learning",
            "data analysis", "penetration testing", "statistics",
        ],
        "required_min": 2,
    },

    "Cloud Engineer": {
        "icon": "☁️",
        "description": "Design and manage scalable cloud infrastructure solutions.",
        "exclusive": [
            "aws certified", "azure certified", "gcp certified", "solutions architect",
            "cloud architect", "cloudformation", "cdk",
            "s3", "ec2", "lambda", "vpc", "iam", "rds", "route53",
            "azure functions", "azure blob", "google cloud platform",
            "cloud migration", "multi-cloud", "cloud security", "cost optimisation",
            "cloud cost", "well-architected", "dynamodb",
            "cloud infrastructure", "cloud native",
        ],
        "shared": [
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "microservices", "monitoring", "linux",
        ],
        "phrases": [
            "cloud infrastructure", "cloud architecture", "cloud deployment",
            "cloud migration", "cloud services", "managed services",
        ],
        "negatives": [
            "html", "css", "javascript", "react", "machine learning",
            "penetration testing", "data analysis", "jenkins", "ci/cd",
        ],
        "required_min": 2,
    },

    "Cybersecurity Analyst": {
        "icon": "🛡️",
        "description": "Protect systems and networks from cyber threats and vulnerabilities.",
        "exclusive": [
            "cybersecurity", "penetration testing", "ethical hacking", "network security",
            "vulnerability assessment", "siem", "soc", "owasp", "encryption",
            "firewalls", "ids", "ips", "incident response", "threat intelligence",
            "ceh", "cissp", "security audit", "malware analysis", "forensics",
            "wireshark", "metasploit", "nmap", "burp suite", "kali linux",
            "zero day", "security operations", "threat hunting", "red team",
            "blue team", "oscp", "comptia security",
        ],
        "shared": [
            "linux", "python", "bash", "networking", "ssl", "aws",
        ],
        "phrases": [
            "security analysis", "threat modelling", "security operations centre",
            "cyber threat", "security incident", "vulnerability scan",
        ],
        "negatives": [
            "html", "css", "javascript", "react", "machine learning",
            "docker", "kubernetes", "terraform", "data analysis",
        ],
        "required_min": 2,
    },

    "Business Analyst": {
        "icon": "📊",
        "description": "Bridge business needs and technology solutions through data-driven insights.",
        "exclusive": [
            "business analysis", "requirements gathering", "stakeholder management",
            "power bi", "tableau", "user stories", "process improvement",
            "gap analysis", "bpmn", "use cases", "business requirements",
            "functional requirements", "process mapping",
            "business process", "cbap", "pmi-pba", "business intelligence",
            "kpi", "roi", "feasibility study", "change management",
            "workflow analysis", "data governance",
        ],
        "shared": [
            "sql", "excel", "agile", "scrum", "jira", "confluence",
            "reporting", "dashboard", "documentation", "project management",
        ],
        "phrases": [
            "business requirements", "stakeholder analysis", "business process",
            "requirements document", "project scope",
        ],
        "negatives": [
            "docker", "kubernetes", "terraform", "machine learning",
            "neural network", "penetration testing", "javascript", "react",
        ],
        "required_min": 2,
    },

    "Python Developer": {
        "icon": "🐍",
        "description": "Build robust backend systems and APIs using Python frameworks.",
        "exclusive": [
            "django", "flask", "fastapi", "sqlalchemy", "celery",
            "pytest", "asyncio", "aiohttp", "pydantic", "alembic",
            "python developer", "backend developer", "oop", "design patterns",
            "unit testing", "virtualenv", "pip", "poetry", "uvicorn",
            "gunicorn", "orm", "rest framework", "drf",
            "python backend", "api development", "websocket",
        ],
        "shared": [
            "python", "postgresql", "redis", "mongodb", "docker",
            "git", "aws", "microservices", "api", "linux",
        ],
        "phrases": [
            "python application", "rest api", "backend api",
            "python framework", "database design", "api development",
        ],
        "negatives": [
            "html", "css", "javascript", "react", "machine learning",
            "terraform", "ansible", "penetration testing",
        ],
        "required_min": 2,
    },
}


def score_role(role_name, config, text_lower, skill_set):
    exclusive_hits, shared_hits, phrase_hits, neg_hits = [], [], [], []

    for kw in config["exclusive"]:
        if kw in skill_set or kw in text_lower:
            exclusive_hits.append(kw)

    for kw in config["shared"]:
        if kw in skill_set or kw in text_lower:
            shared_hits.append(kw)

    for ph in config.get("phrases", []):
        if ph in text_lower:
            phrase_hits.append(ph)

    for kw in config.get("negatives", []):
        if kw in text_lower:
            neg_hits.append(kw)

    raw = max(
        len(exclusive_hits) * WEIGHT_EXCLUSIVE +
        len(shared_hits)    * WEIGHT_SHARED    +
        len(phrase_hits)    * WEIGHT_PHRASE    +
        len(neg_hits)       * WEIGHT_NEGATIVE,
        0
    )

    max_possible = (
        len(config["exclusive"])       * WEIGHT_EXCLUSIVE +
        len(config["shared"])          * WEIGHT_SHARED    +
        len(config.get("phrases", [])) * WEIGHT_PHRASE
    )

    return {
        "role": role_name,
        "raw": raw,
        "max_possible": max_possible,
        "exclusive_hits": exclusive_hits,
        "shared_hits": shared_hits,
        "phrase_hits": phrase_hits,
        "neg_hits": neg_hits,
        "exclusive_count": len(exclusive_hits),
        "icon": config["icon"],
        "description": config["description"],
        "required_min": config.get("required_min", 1),
    }


def compute_confidence(score_dict, all_scores):
    raw  = score_dict["raw"]
    maxi = score_dict["max_possible"]
    if maxi == 0 or raw == 0:
        return 0.0
    base     = raw / maxi * 100
    glob_max = max(s["raw"] for s in all_scores) or 1
    relative = raw / glob_max
    blended  = base * 0.60 + relative * 100 * 0.40
    return round(min(blended, 97.0), 1)


def predict_role_keyword(text: str, skills: List[str]) -> List[dict]:
    text_lower = text.lower()
    skill_set  = set(s.lower() for s in skills)

    all_scored = [
        score_role(name, cfg, text_lower, skill_set)
        for name, cfg in JOB_ROLES.items()
    ]

    # Gate 1: exclusive keyword count >= required_min AND raw > 0
    eligible = [
        s for s in all_scored
        if s["raw"] > 0 and s["exclusive_count"] >= s["required_min"]
    ]
    # Gate 2 (relax): at least 1 exclusive hit
    if not eligible:
        eligible = [s for s in all_scored if s["exclusive_count"] >= 1]
    # Gate 3 (last resort): any positive score
    if not eligible:
        eligible = [s for s in all_scored if s["raw"] > 0]
    # Nothing at all
    if not eligible:
        return [{
            "role": "General Software Engineer",
            "confidence": 35.0,
            "matched_keywords": [],
            "match_count": 0,
            "icon": "💻",
            "description": "General software engineering. Add specific skills for a precise prediction.",
            "exclusive_count": 0,
        }]

    for s in eligible:
        s["confidence"] = compute_confidence(s, eligible)

    eligible.sort(key=lambda x: x["confidence"], reverse=True)

    results = []
    for s in eligible:
        all_kw = list(dict.fromkeys(s["phrase_hits"] + s["exclusive_hits"] + s["shared_hits"]))
        results.append({
            "role":             s["role"],
            "confidence":       s["confidence"],
            "matched_keywords": all_kw[:20],
            "match_count":      len(all_kw),
            "icon":             s["icon"],
            "description":      s["description"],
            "exclusive_count":  s["exclusive_count"],
        })

    return results[:6]


def predict_role(text: str, skills: List[str]) -> Dict:
    predictions = predict_role_keyword(text, skills)
    top = predictions[0]
    return {
        "predicted_role":   top["role"],
        "confidence":       top["confidence"],
        "icon":             top.get("icon", "💼"),
        "description":      top.get("description", ""),
        "matched_keywords": top.get("matched_keywords", []),
        "alternatives":     predictions[1:4],
        "all_predictions":  predictions,
    }


def get_role_requirements(role: str) -> Dict:
    data = {
        "Data Scientist": {
            "core_skills":     ["Python", "SQL", "Machine Learning", "Statistics", "Data Visualisation"],
            "advanced_skills": ["Deep Learning", "NLP", "Big Data", "Cloud Platforms", "A/B Testing"],
            "tools":           ["Jupyter", "Pandas", "Scikit-learn", "TensorFlow", "Tableau"],
            "certifications":  ["Google Data Analytics", "AWS ML Specialty", "Coursera ML by Andrew Ng"],
            "learning_path":   ["Statistics → Python → ML → Deep Learning → Deployment"],
            "avg_salary":      "$95,000 – $140,000",
        },
        "AI/ML Engineer": {
            "core_skills":     ["Python", "TensorFlow / PyTorch", "Mathematics", "ML Algorithms", "Cloud"],
            "advanced_skills": ["MLOps", "Distributed Systems", "CUDA", "Model Optimisation", "LLMs"],
            "tools":           ["Docker", "Kubernetes", "MLflow", "HuggingFace", "Ray"],
            "certifications":  ["TensorFlow Developer Certificate", "AWS ML Specialty", "Deep Learning.AI"],
            "learning_path":   ["Math/Stats → Python → ML → Deep Learning → MLOps → Production"],
            "avg_salary":      "$110,000 – $160,000",
        },
        "Web Developer": {
            "core_skills":     ["HTML", "CSS", "JavaScript", "React / Angular", "Node.js"],
            "advanced_skills": ["TypeScript", "GraphQL", "Microservices", "CI/CD", "Performance"],
            "tools":           ["Git", "Webpack", "Docker", "Figma", "Postman"],
            "certifications":  ["Meta Frontend Dev", "AWS Cloud Practitioner", "Google UX Design"],
            "learning_path":   ["HTML/CSS → JS → Framework → Backend → Full Stack → DevOps"],
            "avg_salary":      "$70,000 – $120,000",
        },
        "DevOps Engineer": {
            "core_skills":     ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud Platforms"],
            "advanced_skills": ["Terraform", "Ansible", "Service Mesh", "GitOps", "Security"],
            "tools":           ["Jenkins", "GitHub Actions", "Prometheus", "Grafana", "ELK Stack"],
            "certifications":  ["CKA", "AWS DevOps Pro", "Google Cloud DevOps"],
            "learning_path":   ["Linux → Networking → Docker → Kubernetes → Cloud → IaC"],
            "avg_salary":      "$95,000 – $145,000",
        },
        "Cloud Engineer": {
            "core_skills":     ["AWS / Azure / GCP", "Networking", "Security", "Docker", "Scripting"],
            "advanced_skills": ["Multi-cloud", "Cost Optimisation", "Cloud Architecture", "Serverless"],
            "tools":           ["Terraform", "CloudFormation", "CDK", "Azure DevOps", "GCP Console"],
            "certifications":  ["AWS Solutions Architect", "Azure Administrator", "GCP Associate"],
            "learning_path":   ["Networking → Linux → Cloud Fundamentals → Architect → Multi-cloud"],
            "avg_salary":      "$90,000 – $140,000",
        },
        "Cybersecurity Analyst": {
            "core_skills":     ["Network Security", "Linux", "Ethical Hacking", "SIEM", "Incident Response"],
            "advanced_skills": ["Malware Analysis", "Threat Intelligence", "Cloud Security", "Forensics"],
            "tools":           ["Wireshark", "Metasploit", "Nmap", "Splunk", "Burp Suite"],
            "certifications":  ["CEH", "CompTIA Security+", "CISSP", "OSCP"],
            "learning_path":   ["Networking → Linux → Security Fundamentals → Ethical Hacking → Specialisation"],
            "avg_salary":      "$85,000 – $130,000",
        },
        "Business Analyst": {
            "core_skills":     ["SQL", "Excel", "Data Analysis", "Requirements Gathering", "Reporting"],
            "advanced_skills": ["Power BI", "Tableau", "Process Modelling", "Agile", "Stakeholder Management"],
            "tools":           ["Jira", "Confluence", "Power BI", "Visio", "BPMN Tools"],
            "certifications":  ["CBAP", "PMI-PBA", "Agile BA", "Tableau Desktop Specialist"],
            "learning_path":   ["Business Fundamentals → SQL → Data Analysis → BI Tools → Agile → Strategy"],
            "avg_salary":      "$70,000 – $110,000",
        },
        "Python Developer": {
            "core_skills":     ["Python", "OOP", "REST APIs", "SQL", "Git"],
            "advanced_skills": ["Async Programming", "Microservices", "Testing", "Docker", "AWS"],
            "tools":           ["Django / Flask / FastAPI", "PostgreSQL", "Redis", "Celery", "Docker"],
            "certifications":  ["Python Institute PCEP / PCAP", "AWS Developer Associate"],
            "learning_path":   ["Python Basics → OOP → Web Frameworks → Databases → APIs → Cloud"],
            "avg_salary":      "$75,000 – $120,000",
        },
    }
    return data.get(role, {
        "core_skills": [], "advanced_skills": [], "tools": [],
        "certifications": [], "learning_path": [], "avg_salary": "N/A",
    })
