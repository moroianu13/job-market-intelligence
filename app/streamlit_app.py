#!/usr/bin/env python3
"""
Job Market Intelligence Dashboard

Production-grade Streamlit dashboard for exploring tech job market data.
Features: Interactive filtering, role/skills analysis, salary insights, 
and ML vs rule-based classification comparison.

Audience: CS professionals, technical recruiters, ML engineers.
"""
import random
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="▲",  # Simple triangle, professional
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional color palette
COLOR_PRIMARY = "#2E5090"      # Professional blue
COLOR_SECONDARY = "#547DBF"    # Lighter blue
COLOR_ACCENT = "#E8A60C"       # Subtle gold accent
COLOR_SUCCESS = "#10A37F"      # Professional green
COLOR_WARNING = "#D97706"      # Professional amber
COLOR_NEUTRAL = "#6B7280"      # Professional gray

# Resource guards
ALLOWED_COLUMNS = [
    'job_id', 'title', 'description', 'created', 'redirect_url', 'company', 'category',
    'location', 'salary_min', 'salary_max', 'run_date', 'country', 'query',
    'roles', 'skills', 'salary_flag', 'salary_note', 'job_fingerprint'
]
MAX_ROWS = 50000
CACHE_TTL_SECONDS = 600

# Custom CSS for professional styling
st.markdown(f"""
<style>
    /* Main headers */
    .page-header {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
        margin-bottom: 0.5rem;
        letter-spacing: -0.01em;
    }}
    
    .page-subheader {{
        font-size: 0.95rem;
        color: {COLOR_NEUTRAL};
        font-weight: 500;
        margin-bottom: 2rem;
    }}
    
    /* Section headers */
    .section-header {{
        font-size: 1.3rem;
        font-weight: 600;
        color: {COLOR_PRIMARY};
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }}
    
    /* KPI Cards styling */
    .kpi-card {{
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-left: 3px solid {COLOR_PRIMARY};
        padding: 1.5rem;
        border-radius: 0.5rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
        margin-bottom: 0.25rem;
    }}
    
    .kpi-label {{
        font-size: 0.85rem;
        color: {COLOR_NEUTRAL};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Divider */
    .divider {{
        margin: 2rem 0;
        border: 0;
        border-top: 1px solid #e5e7eb;
    }}
    
    /* Info boxes */
    .info-box {{
        background-color: #f0f9ff;
        border-left: 4px solid {COLOR_PRIMARY};
        padding: 1rem;
        border-radius: 0.375rem;
        font-size: 0.9rem;
    }}
    
    /* Table styling */
    .stDataFrame {{
        font-size: 0.9rem;
    }}
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {{
        .kpi-card {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-left-color: {COLOR_SECONDARY};
        }}
        
        .kpi-value {{
            color: {COLOR_SECONDARY};
        }}
        
        .page-header {{
            color: {COLOR_SECONDARY};
        }}
        
        .section-header {{
            color: {COLOR_SECONDARY};
        }}
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load and cache job market data from parquet file.
    
    Args:
        file_path: Path to parquet file
        
    Returns:
        DataFrame with roles/skills as lists, or None if error
    """
    try:
        df = pd.read_parquet(file_path)
        # Restrict to allowed columns to avoid loading unexpected data
        allowed = [c for c in df.columns if c in ALLOWED_COLUMNS]
        df = df[allowed]
        for col in ('roles', 'skills'):
            if col not in df.columns:
                df[col] = []
        # Cap rows to prevent resource exhaustion on large files
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            st.warning(
                f"Dataset truncated to first {MAX_ROWS:,} rows to protect app resources.",
                icon="⚠️"
            )
        # Handle numpy arrays in roles/skills columns
        df['roles'] = df['roles'].apply(lambda x: list(x) if hasattr(x, '__iter__') else [])
        df['skills'] = df['skills'].apply(lambda x: list(x) if hasattr(x, '__iter__') else [])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_kpi_cards(df: pd.DataFrame) -> None:
    """
    Render KPI metric cards in a 4-column grid.
    
    Displays: Total Jobs, Countries, Salary Coverage, Skills Coverage
    
    Args:
        df: Filtered jobs DataFrame
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{len(df):,}</div>
            <div class="kpi-label">Total Jobs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{df['country'].nunique()}</div>
            <div class="kpi-label">Countries</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        salary_coverage = 100 * df['salary_min'].notna().sum() / max(len(df), 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{salary_coverage:.1f}%</div>
            <div class="kpi-label">Salary Coverage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        skills_coverage = 100 * df['skills'].apply(lambda x: len(x) > 0).sum() / max(len(df), 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{skills_coverage:.1f}%</div>
            <div class="kpi-label">Skills Coverage</div>
        </div>
        """, unsafe_allow_html=True)


def render_overview(df: pd.DataFrame) -> None:
    """
    Render Overview tab with country distribution, timeline, and summary stats.
    
    Args:
        df: Filtered jobs DataFrame
    """
    st.markdown('<p class="section-header">Dataset Overview</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Country Distribution")
        country_counts = df['country'].value_counts().head(15)
        
        fig = px.bar(
            x=country_counts.index.str.upper(),
            y=country_counts.values,
            labels={'x': '', 'y': 'Number of Jobs'},
            color_discrete_sequence=[COLOR_PRIMARY],
            height=400
        )
        fig.update_layout(
            showlegend=False,
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
        st.plotly_chart(fig, use_container_width=True, key='overview_country_dist')
        st.caption("Top 15 countries by job count")
    
    with col2:
        st.markdown("### Timeline")
        if 'run_date' in df.columns and df['run_date'].notna().any():
            date_counts = df['run_date'].value_counts().sort_index()
            
            fig = px.line(
                x=date_counts.index,
                y=date_counts.values,
                labels={'x': 'Date', 'y': 'Jobs Posted'},
                color_discrete_sequence=[COLOR_SECONDARY],
                height=400,
                markers=True
            )
            fig.update_layout(
                showlegend=False,
                hovermode='x unified',
                margin=dict(l=0, r=0, t=30, b=0)
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
            st.plotly_chart(fig, use_container_width=True, key='overview_timeline')
            st.caption("Jobs indexed over time")
        else:
            st.info("Timeline data not available in this dataset")
    
    # Summary stats table
    st.markdown("---")
    st.markdown("### Dataset Statistics")
    
    summary_data = {
        'Metric': [
            'Total Job Postings',
            'Unique Companies',
            'Jobs with Salary Info',
            'Jobs with Skills Extracted',
            'Multi-Role Positions'
        ],
        'Count': [
            f"{len(df):,}",
            f"{df['company'].nunique():,}",
            f"{df['salary_min'].notna().sum():,}",
            f"{df['skills'].apply(lambda x: len(x) > 0).sum():,}",
            f"{df['roles'].apply(lambda x: len(x) > 1).sum():,}"
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


def render_roles_skills(df: pd.DataFrame) -> None:
    """
    Render Roles & Skills analysis with distributions and top skills.
    
    Args:
        df: Filtered jobs DataFrame
    """
    st.markdown('<p class="section-header">Roles & Skills Analysis</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Role Distribution
    with col1:
        st.markdown("### Role Distribution")
        role_counts = Counter([r for roles in df['roles'] for r in roles])
        
        if role_counts:
            role_df = pd.DataFrame(
                sorted(role_counts.items(), key=lambda x: x[1], reverse=True),
                columns=['Role', 'Count']
            )
            role_df = role_df.head(12)
            role_df['Role'] = role_df['Role'].str.replace('_', ' ').str.title()
            
            fig = px.bar(
                role_df.iloc[::-1],
                y='Role',
                x='Count',
                orientation='h',
                color_discrete_sequence=[COLOR_PRIMARY],
                height=400
            )
            fig.update_layout(
                showlegend=False,
                hovermode='y unified',
                margin=dict(l=150, r=0, t=30, b=0),
                xaxis_title='',
                yaxis_title=''
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
            st.plotly_chart(fig, use_container_width=True, key='roles_distribution')
            st.caption(f"Top 12 roles (out of {len(role_counts)} total)")
        else:
            st.info("No role data available")
    
    # Top Skills
    with col2:
        st.markdown("### Top Skills")
        top_n = st.slider("Number of skills to display", min_value=10, max_value=50, value=15, step=5)
        
        all_skills = [s for skills in df['skills'] for s in skills if len(skills) > 0]
        
        if all_skills:
            skill_counts = Counter(all_skills)
            skill_df = pd.DataFrame(
                skill_counts.most_common(top_n),
                columns=['Skill', 'Count']
            )
            
            fig = px.bar(
                skill_df.iloc[::-1],
                y='Skill',
                x='Count',
                orientation='h',
                color_discrete_sequence=[COLOR_SECONDARY],
                height=400
            )
            fig.update_layout(
                showlegend=False,
                hovermode='y unified',
                margin=dict(l=100, r=0, t=30, b=0),
                xaxis_title='',
                yaxis_title=''
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
            st.plotly_chart(fig, use_container_width=True, key='skills_distribution')
            st.caption(f"Top {top_n} in-demand skills")
        else:
            st.info("No skills data available for filtered jobs")


def render_salaries(df: pd.DataFrame) -> None:
    """
    Render salary analysis with distribution, statistics, and by-country breakdown.
    
    Uses only clean salary data (salary_flag == 'ok') for analysis.
    
    Args:
        df: Filtered jobs DataFrame
    """
    st.markdown('<p class="section-header">Compensation Analysis</p>', unsafe_allow_html=True)
    
    # Check if salary validation has been applied
    has_validation = 'salary_flag' in df.columns
    
    # Filter to clean salary data if validation exists
    if has_validation:
        df_salary = df[
            (df['salary_flag'] == 'ok') & 
            df['salary_min'].notna() & 
            df['salary_max'].notna()
        ].copy()
        
        # Show quality warning if needed
        flagged_count = len(df[df['salary_flag'] != 'ok'])
        if flagged_count > 0:
            with st.expander("ℹ️ Data Quality Note", expanded=False):
                st.markdown(f"""
                **Salary data has been validated for quality.**
                
                - Clean records used: {len(df_salary):,}
                - Flagged/excluded: {flagged_count:,}
                
                Excluded reasons: missing data, low sample size, outliers, possible B2B rates.
                """)
    else:
        # Fallback: no validation applied
        df_salary = df[df['salary_min'].notna() & df['salary_max'].notna()].copy()
    
    if len(df_salary) > 0:
        df_salary['salary_mid'] = (df_salary['salary_min'] + df_salary['salary_max']) / 2
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Salary", f"€{df_salary['salary_mid'].mean():,.0f}")
        with col2:
            st.metric("Median Salary", f"€{df_salary['salary_mid'].median():,.0f}")
        with col3:
            st.metric("Min Salary", f"€{df_salary['salary_mid'].min():,.0f}")
        with col4:
            st.metric("Max Salary", f"€{df_salary['salary_mid'].max():,.0f}")
        
        # Distribution
        st.markdown("---")
        st.markdown("### Salary Distribution")
        
        fig = px.histogram(
            df_salary,
            x='salary_mid',
            nbins=40,
            color_discrete_sequence=[COLOR_PRIMARY],
            labels={'salary_mid': 'Salary (€)', 'count': 'Jobs'},
            height=400
        )
        fig.update_layout(
            showlegend=False,
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
        st.plotly_chart(fig, use_container_width=True, key='salary_histogram')
        st.caption(f"Distribution of {len(df_salary):,} jobs with validated salary data")
        
        # By Country
        st.markdown("---")
        st.markdown("### Average Salary by Country")
        
        salary_by_country = (
            df_salary.groupby('country')['salary_mid']
            .agg(['mean', 'median', 'count'])
            .reset_index()
        )
        
        # Apply minimum sample size threshold (10 records per country)
        min_samples = 10
        salary_by_country = salary_by_country[salary_by_country['count'] >= min_samples]
        salary_by_country = salary_by_country.sort_values('mean', ascending=True)
        
        if len(salary_by_country) > 0:
            fig = px.bar(
                salary_by_country,
                y='country',
                x='mean',
                color='count',
                orientation='h',
                color_continuous_scale='Blues',
                labels={'mean': 'Avg Salary (€)', 'country': '', 'count': 'Jobs'},
                height=max(300, len(salary_by_country) * 20)
            )
            fig.update_layout(
                showlegend=True,
                hovermode='y unified',
                margin=dict(l=50, r=0, t=30, b=0),
                xaxis_title='Average Salary (€)',
                yaxis_title=''
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
            st.plotly_chart(fig, use_container_width=True, key='salary_by_country')
            st.caption(f"Based on {len(salary_by_country)} countries with {min_samples}+ validated records")
        else:
            st.info(f"No countries have {min_samples}+ validated salary records")
        
    else:
        st.info("No salary data available for filtered jobs. This may be normal for rule-based labeling.")


def render_ml_comparison(df_rules: pd.DataFrame, df_ml: pd.DataFrame) -> None:
    """
    Render ML vs Rule-based classification comparison.
    
    Shows agreement statistics, example differences, and highlights
    what the ML model adds/removes compared to rule-based approach.
    
    Args:
        df_rules: Rule-based labeled DataFrame
        df_ml: ML-labeled DataFrame
    """
    st.markdown('<p class="section-header">Classification Approaches: Comparison</p>', unsafe_allow_html=True)
    
    # Sync indices if needed
    min_len = min(len(df_rules), len(df_ml))
    if len(df_rules) != len(df_ml):
        st.warning(f"Dataset sizes differ. Using first {min_len} records.")
        df_rules = df_rules.iloc[:min_len].copy()
        df_ml = df_ml.iloc[:min_len].copy()
    
    # Calculate agreement
    df_rules['roles_str'] = df_rules['roles'].apply(lambda x: ','.join(sorted(x)))
    df_ml['roles_str'] = df_ml['roles'].apply(lambda x: ','.join(sorted(x)))
    
    agreement_mask = df_rules['roles_str'] == df_ml['roles_str']
    agreement_count = agreement_mask.sum()
    agreement_pct = 100 * agreement_count / len(df_rules)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Agreement", f"{agreement_pct:.1f}%")
    with col2:
        st.metric("Agreed", f"{agreement_count:,}")
    with col3:
        st.metric("Differences", f"{len(df_rules) - agreement_count:,}")
    with col4:
        st.metric("Total Records", f"{len(df_rules):,}")
    
    # Explanation
    st.markdown("---")
    st.markdown("""
    ### How These Approaches Differ
    
    **Rule-Based Classification** extracts roles using pattern matching and heuristics. 
    Fast, deterministic, and transparent — you see exactly why a job gets labeled.
    
    **ML Classification** trains on examples to recognize role mentions more flexibly. 
    Can catch subtle patterns but requires labeled training data and periodic retraining.
    
    The comparison below shows where they diverge.
    """)
    
    st.markdown("---")
    st.markdown("### Sample Differences")
    
    # Show disagreement samples
    disagreements = df_rules[~agreement_mask].index.tolist()
    
    if disagreements:
        n_samples = st.slider("Examples to show", min_value=2, max_value=min(15, len(disagreements)), value=5)
        sample_indices = disagreements[:n_samples]
        
        for i, idx in enumerate(sample_indices, 1):
            job_rules = df_rules.iloc[idx]
            job_ml = df_ml.iloc[idx]
            
            with st.expander(f"{i}. {job_rules['title'][:70]}... ({job_rules['country'].upper()})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Rule-Based Output**")
                    roles_rules = [r.replace('_', ' ').title() for r in job_rules['roles']]
                    st.write(", ".join(roles_rules) if roles_rules else "*(no roles detected)*")
                
                with col2:
                    st.markdown("**ML Model Output**")
                    roles_ml = [r.replace('_', ' ').title() for r in job_ml['roles']]
                    st.write(", ".join(roles_ml) if roles_ml else "*(no roles detected)*")
                
                # Highlight differences
                set_rules = set(job_rules['roles'])
                set_ml = set(job_ml['roles'])
                added = set_ml - set_rules
                removed = set_rules - set_ml
                
                if added:
                    added_text = ", ".join([r.replace('_', ' ').title() for r in added])
                    st.success(f"ML added: {added_text}")
                if removed:
                    removed_text = ", ".join([r.replace('_', ' ').title() for r in removed])
                    st.error(f"ML removed: {removed_text}")
                
                with st.expander("Context"):
                    st.write(f"**Company**: {job_rules['company']}")
                    if pd.notna(job_rules['salary_min']):
                        st.write(f"**Salary**: €{job_rules['salary_min']:,.0f} – €{job_rules['salary_max']:,.0f}")
                    if len(job_rules['skills']) > 0:
                        st.write(f"**Skills**: {', '.join(job_rules['skills'][:8])}")
    else:
        st.info("No disagreements found — both methods agree on all samples!")


def render_job_table(df: pd.DataFrame) -> None:
    """
    Render paginated job listings table.
    
    Displays: Title, Country, Company, Roles, Skills, Salary Range
    Includes: Page size selector, pagination controls
    
    Args:
        df: Filtered jobs DataFrame
    """
    st.markdown('<p class="section-header">Job Listings</p>', unsafe_allow_html=True)
    st.markdown("Browse and search through available job postings")
    
    if len(df) == 0:
        st.info("No jobs match the current filters")
        return
    
    # Prepare display columns
    display_df = df[[
        'title', 'country', 'company', 'roles', 'skills', 'salary_min', 'salary_max'
    ]].copy()
    
    display_df['roles'] = display_df['roles'].apply(
        lambda x: ', '.join([r.replace('_', ' ').title() for r in x]) if x else '-'
    )
    display_df['skills'] = display_df['skills'].apply(
        lambda x: ', '.join(x[:4]) + ('...' if len(x) > 4 else '') if x else '-'
    )
    display_df['country'] = display_df['country'].str.upper()
    display_df['salary'] = display_df.apply(
        lambda row: f"€{row['salary_min']:,.0f} – €{row['salary_max']:,.0f}"
        if pd.notna(row['salary_min']) else '—',
        axis=1
    )
    
    display_df = display_df.drop(columns=['salary_min', 'salary_max'])
    display_df.columns = ['Title', 'Country', 'Company', 'Roles', 'Skills', 'Salary Range']
    
    # Pagination
    col_pagesize, col_search = st.columns([1, 4])
    
    with col_pagesize:
        page_size = st.selectbox(
            "Rows per page",
            options=[10, 25, 50, 100],
            index=1,
            label_visibility="collapsed"
        )
    
    total_pages = (len(display_df) + page_size - 1) // page_size
    
    with col_search:
        page_num = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            label_visibility="collapsed"
        )
    
    # Slice and display
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    page_data = display_df.iloc[start_idx:end_idx]
    
    st.dataframe(page_data, use_container_width=True, hide_index=True, height=500)
    
    st.caption(
        f"Page {page_num} of {total_pages} "
        f"(showing {len(page_data):,} of {len(display_df):,} jobs)"
    )


def render_about() -> None:
    """
    Render footer with system information and methodology.
    """
    st.markdown("---")
    st.markdown('<p style="font-size: 0.9rem; color: #6B7280;">About This System</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Data Pipeline**
        
        • Scrapes job postings from Adzuna API
        • Normalizes company names & salaries
        • Extracts structured metadata
        • Detects and flags reposted jobs
        """)
    
    with col2:
        st.markdown("""
        **Classification Methods**
        
        • **Rules-Based**: Pattern matching on job text (fast, transparent)
        • **ML Model**: Gradient boosting trained on hand-labeled samples
        • Updated weekly with new postings
        """)
    
    with col3:
        st.markdown("""
        **Key Features**
        
        • Ghost job detection (unreliable postings)
        • Multi-role position identification
        • Salary normalization across currencies
        • Skills extraction via NLP
        """)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """
    Main application entry point.
    Manages state, filters, and renders all dashboard components.
    """
    
    # Header
    st.markdown('<p class="page-header">Job Market Intelligence</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">Interactive analysis of tech job market across Europe</p>', unsafe_allow_html=True)
    
    # Sidebar - Data source selection
    st.sidebar.markdown("### Data Source")
    
    default_paths = [
        "data/curated/jobs_all_labeled.parquet",
        "data/curated/jobs_all_labeled_ml.parquet"
    ]
    
    available_files = [p for p in default_paths if Path(p).exists()]
    
    if not available_files:
        st.error("No data files found. Run: `python orchestration/run_pipeline.py --all`")
        return
    
    selected_file = st.sidebar.selectbox(
        "Classification Method",
        available_files,
        format_func=lambda x: "Machine Learning" if "ml" in x else "Rule-Based"
    )
    
    # Load data
    df = load_data(selected_file)
    
    if df is None or len(df) == 0:
        st.error("Failed to load data")
        return
    
    # Sidebar filters
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    
    # Country filter
    all_countries = sorted(df['country'].unique())
    selected_countries = st.sidebar.multiselect(
        "Countries",
        all_countries,
        default=all_countries,
        placeholder="Select countries..."
    )
    
    # Role filter
    all_roles = sorted(set([r for roles in df['roles'] for r in roles]))
    selected_roles = st.sidebar.multiselect(
        "Roles",
        all_roles,
        placeholder="All roles",
        help="Leave empty to include all roles"
    )
    
    # Salary filter
    has_salary = st.sidebar.checkbox("Salary data only", value=False)
    
    # Apply filters
    df_filtered = df[df['country'].isin(selected_countries)].copy()
    
    if selected_roles:
        df_filtered = df_filtered[
            df_filtered['roles'].apply(lambda x: any(r in selected_roles for r in x))
        ]
    
    if has_salary:
        df_filtered = df_filtered[df_filtered['salary_min'].notna()]
    
    # Filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    **Results**: {len(df_filtered):,} / {len(df):,} jobs
    
    Filtered by:
    - {len(selected_countries)} / {len(all_countries)} countries
    - {len(selected_roles) if selected_roles else 'All'} roles
    - Salary: {'Yes' if has_salary else 'No filter'}
    """)
    
    # KPI Cards
    st.markdown("---")
    render_kpi_cards(df_filtered)
    
    # Main tabs
    tab_overview, tab_roles, tab_salaries, tab_ml, tab_jobs = st.tabs([
        "Overview",
        "Roles & Skills",
        "Compensation",
        "Methods",
        "Job Listings"
    ])
    
    with tab_overview:
        render_overview(df_filtered)
    
    with tab_roles:
        render_roles_skills(df_filtered)
    
    with tab_salaries:
        render_salaries(df_filtered)
    
    with tab_ml:
        # Check if both datasets exist for comparison
        ml_file = "data/curated/jobs_all_labeled_ml.parquet"
        rules_file = "data/curated/jobs_all_labeled.parquet"
        
        if Path(ml_file).exists() and Path(rules_file).exists():
            df_ml = load_data(ml_file)
            df_rules = load_data(rules_file)
            
            if df_ml is not None and df_rules is not None:
                render_ml_comparison(df_rules, df_ml)
            else:
                st.error("Failed to load comparison datasets")
        else:
            st.info("""
            ML comparison requires both rule-based and ML-labeled datasets.
            
            **To enable:**
            ```bash
            python orchestration/run_pipeline.py --all
            python ml/role_classifier/train_classifier.py
            python orchestration/run_pipeline.py --label --ml
            ```
            """)
    
    with tab_jobs:
        render_job_table(df_filtered)
    
    # Footer
    st.markdown("---")
    render_about()


if __name__ == '__main__':
    main()
