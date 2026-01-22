from processing.skill_extraction import extract_skills


def test_extract_skills_basic():
    skills = extract_skills(
        "Data Engineer",
        "We use Python, SQL, Airflow, Spark and Docker on AWS."
    )
    assert "python" in skills
    assert "sql" in skills
    assert "airflow" in skills
    assert "spark" in skills
    assert "docker" in skills
    assert "aws" in skills


def test_extract_skills_empty():
    assert extract_skills("", "") == []


def test_extract_skills_case_insensitive():
    skills = extract_skills("ML Engineer", "Experience with PyTorch and TensorFlow.")
    assert "pytorch" in skills
    assert "tensorflow" in skills
