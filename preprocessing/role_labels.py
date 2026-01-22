"""Role classification module.

Defines role categories and keyword-based classification logic for job postings.
"""
import re


ROLES = {
    "data_scientist",
    "data_engineer",
    "machine_learning_engineer",
    "data_analyst",
    "cybersecurity_specialist",
    "devops_engineer",
    "software_engineer",
    "other",
}

ROLE_KEYWORDS = {
    "data_scientist": [
        r"data scientist", 
        r"applied scientist",
        r"research scientist",
    ],
    "data_engineer": [
        r"data engineer",
        r"analytics engineer",
        r"etl developer",
        r"big data engineer",
        r"big data administrator",
        r"data platform engineer",
        r"reporting engineer",
        r"gis.*engineer",
        r"database engineer",
        r"data warehouse engineer",
    ],
    "machine_learning_engineer": [
        r"machine learning engineer",
        r"ml engineer",
        r"ai engineer",
        r"mlops",
    ],
    "data_analyst": [
        r"data analyst",
        r"business analyst",
        r"analytics analyst",
        r"bi analyst",
        r"reporting analyst",
        r"business intelligence",
    ],
    "cybersecurity_specialist": [
        r"cybersecurity",
        r"security engineer",
        r"security analyst",
        r"infosec",
        r"information security",
    ],
    "devops_engineer": [
        r"devops",
        r"site reliability engineer",
        r"sre",
        r"platform engineer",
        r"infrastructure engineer",
        r"cloud engineer",
        r"systems engineer",
    ],
    "software_engineer": [
        r"software engineer",
        r"software developer",
        r"backend engineer",
        r"frontend engineer",
        r"full stack",
        r"fullstack",
        r"web developer",
        r"application developer",
        r"java developer",
        r"python developer",
        r"\.net developer",
    ],
}


def assign_roles(title: str, description: str) -> list[str]:
    """Assign role labels based on job title and description.
    
    Uses keyword pattern matching to classify jobs into one or more role categories.
    If no patterns match, returns ['other'].

    Args:
        title: Job title string
        description: Full job description text

    Returns:
        List of role labels that match the job posting. Returns ['other'] if no matches.
        
    Example:
        >>> assign_roles("Senior Data Scientist", "Work with ML models")
        ['data_scientist']
    """
    if not title:
        return ["other"]
    
    text = f"{title} {description}".lower()
    
    matched_roles: list[str] = []
    
    for role, patterns in ROLE_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                if role in ROLES and role not in matched_roles:
                    matched_roles.append(role)
                break
  
    return matched_roles if matched_roles else ["other"]           
    


    
    
if __name__ == "__main__":
    tests = [
        ("Senior Data Scientist", "Work with ML models"),
        ("Data Engineer", "Build ETL pipelines"),
        ("ML Engineer", "Deploy ML models"),
        ("Business Analyst", "Reporting and dashboards"),
        ("Software Developer", "Backend systems"),
        ("Security Engineer", "Cybersecurity and vulnerability assessment"),
        ("DevOps Engineer", "CI/CD and infrastructure management"),
        ("Random title", "No keywords here"),
    ]
    for title, description in tests:
        print(title, "->", assign_roles(title, description))
        
        
        
