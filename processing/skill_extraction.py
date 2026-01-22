import re
from typing import Dict, List, Pattern, Sequence, Set


SKILL_KEYWORDS: Dict[str, Sequence[str]] = {
    # Languages
    "python": [r"\bpython\b"],
    "sql": [r"\bsql\b", r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\bsqlite\b", r"\bmssql\b", r"\bt-sql\b", r"\bpl/sql\b"],
    "java": [r"\bjava\b"],
    "scala": [r"\bscala\b"],
    "r": [r"\br\b", r"\br language\b", r"\br programming\b"],
    "javascript": [r"\bjavascript\b", r"\bjs\b", r"\bnode\.?js\b"],
    "typescript": [r"\btypescript\b", r"\bts\b"],
    "go": [r"\bgolang\b", r"\bgo\b"],
    "c_plus_plus": [r"\bc\+\+\b", r"\bcpp\b"],
    "rust": [r"\brust\b"],

    # Data / ML libs
    "pandas": [r"\bpandas\b"],
    "numpy": [r"\bnumpy\b"],
    "sklearn": [r"\bscikit[- ]learn\b", r"\bsklearn\b"],
    "pytorch": [r"\bpytorch\b"],
    "tensorflow": [r"\btensorflow\b", r"\btf\b"],
    "keras": [r"\bkeras\b"],
    "xgboost": [r"\bxgboost\b"],
    "lightgbm": [r"\blightgbm\b"],
    "scipy": [r"\bscipy\b"],
    "matplotlib": [r"\bmatplotlib\b"],
    "seaborn": [r"\bseaborn\b"],
    "plotly": [r"\bplotly\b"],

    # DE stack
    "spark": [r"\bspark\b", r"\bpyspark\b", r"\bapache spark\b"],
    "hadoop": [r"\bhadoop\b", r"\bhdfs\b"],
    "airflow": [r"\bairflow\b", r"\bapache airflow\b"],
    "dbt": [r"\bdbt\b", r"\bdata build tool\b"],
    "kafka": [r"\bkafka\b", r"\bapache kafka\b"],
    "databricks": [r"\bdatabricks\b"],
    "snowflake": [r"\bsnowflake\b"],
    "bigquery": [r"\bbigquery\b", r"\bbq\b"],
    "redshift": [r"\bredshift\b", r"\bamazon redshift\b"],
    "flink": [r"\bflink\b", r"\bapache flink\b"],
    "hive": [r"\bhive\b", r"\bapache hive\b"],
    "presto": [r"\bpresto\b", r"\btrino\b"],
    "glue": [r"\baws glue\b", r"\bglue\b"],

    # Databases
    "postgresql": [r"\bpostgres\b", r"\bpostgresql\b"],
    "mongodb": [r"\bmongodb\b", r"\bmongo\b"],
    "redis": [r"\bredis\b"],
    "elasticsearch": [r"\belasticsearch\b", r"\belastic\b"],
    "cassandra": [r"\bcassandra\b"],
    "dynamodb": [r"\bdynamodb\b"],
    "oracle": [r"\boracle\b", r"\boracle db\b"],
    
    # BI / Visualization
    "tableau": [r"\btableau\b"],
    "power_bi": [r"\bpower bi\b", r"\bpowerbi\b"],
    "looker": [r"\blooker\b"],
    "quicksight": [r"\bquicksight\b"],

    # DevOps / Cloud
    "docker": [r"\bdocker\b"],
    "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "terraform": [r"\bterraform\b"],
    "ansible": [r"\bansible\b"],
    "jenkins": [r"\bjenkins\b"],
    "linux": [r"\blinux\b", r"\bunix\b"],
    "git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bversion control\b"],
    "ci_cd": [r"\bci/cd\b", r"\bci[- ]cd\b", r"\bcontinuous integration\b", r"\bgithub actions\b", r"\bgitlab ci\b"],
    "aws": [r"\baws\b", r"\bamazon web services\b"],
    "azure": [r"\bazure\b", r"\bmicrosoft azure\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle cloud\b", r"\bgoogle cloud platform\b"],

    # ML/AI specific
    "mlflow": [r"\bmlflow\b"],
    "kubeflow": [r"\bkubeflow\b"],
    "sagemaker": [r"\bsagemaker\b"],
    "mlops": [r"\bmlops\b"],
    "computer_vision": [r"\bcomputer vision\b", r"\bcv\b"],
    "nlp": [r"\bnlp\b", r"\bnatural language processing\b"],
    "deep_learning": [r"\bdeep learning\b"],
    "machine_learning": [r"\bmachine learning\b", r"\bml\b"],

    # Other tools
    "excel": [r"\bexcel\b", r"\bms excel\b"],
    "api": [r"\bapi\b", r"\brest api\b", r"\brestful\b"],
    "etl": [r"\betl\b"],
    "agile": [r"\bagile\b", r"\bscrum\b"],
}


def _compile_patterns(skill_keywords: Dict[str, Sequence[str]]) -> Dict[str, List[Pattern[str]]]:
    compiled: Dict[str, List[Pattern[str]]] = {}
    for skill, patterns in skill_keywords.items():
        compiled[skill] = [re.compile(p, flags=re.IGNORECASE) for p in patterns]
    return compiled


_COMPILED = _compile_patterns(SKILL_KEYWORDS)


def extract_skills(title: str, description: str) -> List[str]:
    """
    Return a sorted list of detected skills from title+description.
    Uses regex with word boundaries and is case-insensitive.
    """
    text = f"{title or ''} {description or ''}".strip()
    if not text:
        return []

    found: Set[str] = set()
    for skill, patterns in _COMPILED.items():
        if any(p.search(text) for p in patterns):
            found.add(skill)

    return sorted(found)
