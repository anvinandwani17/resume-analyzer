from flask import Flask, render_template, request
import pdfplumber

app = Flask(__name__)

# List of tech skills to detect
KNOWN_SKILLS = [
    "python", "java", "c", "c++",
    "html", "css", "javascript", "react",
    "node", "node.js", "flask", "django",
    "sql", "mysql", "postgres", "mongodb",
    "machine learning", "ml", "deep learning",
    "data analysis", "data analytics",
    "pandas", "numpy", "scikit-learn",
    "git", "github",
    "aws", "azure", "gcp", "cloud",
    "docker", "kubernetes"
]

# Skills we consider "important" for a fresher AI / web / software dev profile
REQUIRED_SKILLS = [
    "python", "html", "css", "javascript",
    "sql", "git", "github", "machine learning"
]

# ---------------------- Helper functions ---------------------- #

def extract_text_from_pdf(file_obj):
    """
    Takes the uploaded PDF file and returns all text as one big string.
    """
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_skills(text):
    """
    Simple skill detection:
    - convert text to lowercase
    - check if each known skill appears in the text
    """
    text_lower = text.lower()
    found = set()

    for skill in KNOWN_SKILLS:
        if skill in text_lower:
            found.add(skill)

    return sorted(list(found))


def has_projects(text):
    """
    Check if the resume mentions projects / systems / models etc.
    """
    keywords = [
        "project", "projects",
        "built", "created", "developed", "designed",
        "implemented", "engineered", "deployed",
        "application", "app", "system", "model"
    ]
    t = text.lower()
    return any(word in t for word in keywords)


def formatting_score(text):
    """
    Gives a simple formatting score out of 20 based on:
    - presence of bullet points
    - presence of common sections like education, skills, projects, etc.
    """
    bullet_chars = ["•", "-", "*"]
    has_bullets = any(char in text for char in bullet_chars)

    sections = ["education", "experience", "skills", "projects", "achievements"]
    section_score = sum(1 for sec in sections if sec in text.lower())

    score = 0

    # Bullet points are good
    if has_bullets:
        score += 8

    # Section usage bonus
    if section_score >= 3:
        score += 12
    elif section_score == 2:
        score += 8
    elif section_score == 1:
        score += 4
    else:
        score += 2

    # Maximum 20
    return min(score, 20)


def calculate_score(extracted_skills, text):
    """
    Calculate total score out of 100 using:
    - Skills match: 50 marks
    - Projects: 30 marks
    - Formatting: 20 marks
    """
    # Skills match score (out of 50)
    matches = sum(1 for skill in REQUIRED_SKILLS if skill in extracted_skills)
    if REQUIRED_SKILLS:
        skill_score = (matches / len(REQUIRED_SKILLS)) * 50
    else:
        skill_score = 0

    # Project score (out of 30)
    project_score = 30 if has_projects(text) else 10  # few marks even if no project keywords

    # Formatting score (out of 20)
    format_score = formatting_score(text)

    total_score = round(skill_score + project_score + format_score, 1)

    return total_score, round(skill_score, 1), project_score, format_score


def generate_suggestions(text, extracted_skills):
    """
    Generate human-readable suggestions to improve the resume.
    """
    suggestions = []

    # Missing important skills
    missing_skills = [s for s in REQUIRED_SKILLS if s not in extracted_skills]
    if missing_skills:
        suggestions.append(
            "Try to add or highlight these important skills if you know them: "
            + ", ".join(missing_skills)
        )

    # If no project-like words
    if not has_projects(text):
        suggestions.append(
            "Add a 'Projects' section with 2–3 good projects. "
            "Mention what you built, tools/technologies used, and your role."
        )

    # Length checking
    word_count = len(text.split())
    if word_count < 150:
        suggestions.append(
            "Your resume looks quite short. Add more details about your skills, projects, and achievements."
        )
    if word_count > 700:
        suggestions.append(
            "Your resume seems long. For a fresher, try to keep it to 1 page with the most important points."
        )

    # No technical skills detected
    if len(extracted_skills) == 0:
        suggestions.append(
            "I could not find a clear 'Skills' section. Add one and list your tools, languages, and frameworks."
        )

    # Bullet points
    bullet_chars = ["•", "-", "*"]
    if not any(char in text for char in bullet_chars):
        suggestions.append(
            "Use bullet points to list skills, projects, and experience instead of big paragraphs. "
            "This makes the resume easier to read."
        )

    if not suggestions:
        suggestions.append(
            "Your resume looks good! You can still refine wording and customize it for each job description."
        )

    return suggestions, missing_skills

# ------------------------- Routes ------------------------- #

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("resume")

        # Basic file checks
        if not file or file.filename == "":
            return render_template("index.html", error="Please upload a PDF file.")

        if not file.filename.lower().endswith(".pdf"):
            return render_template("index.html", error="Only PDF files (.pdf) are supported right now.")

        # Extract text
        text = extract_text_from_pdf(file)

        if not text.strip():
            return render_template("index.html", error="I couldn't read any text from this PDF.")

        # Skill extraction
        extracted_skills = extract_skills(text)

        # Scoring
        total_score, skill_score, project_score, format_score = calculate_score(extracted_skills, text)

        # Suggestions and missing skills
        suggestions, missing_skills = generate_suggestions(text, extracted_skills)

        # Send everything to result page
        return render_template(
            "result.html",
            score=total_score,
            skill_score=skill_score,
            project_score=project_score,
            format_score=format_score,
            skills=extracted_skills,
            missing_skills=missing_skills,
            suggestions=suggestions
        )

    # GET request → just show upload page
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
