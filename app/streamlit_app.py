#!/usr/bin/env python3
"""
Streamlit App for Job Market Intelligence

Interactive dashboard for exploring job market data with filters,
visualizations, and ML vs rule-based comparison.
"""
import random
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

# Page config
st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1f77b4;}
    .sub-header {font-size: 1.5rem; font-weight: 600; margin-top: 1rem;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Load and cache the parquet data."""
    try:
        df = pd.read_parquet(file_path)
        # Handle numpy arrays in roles/skills
        df['roles'] = df['roles'].apply(lambda x: list(x) if hasattr(x, '__iter__') else [])
        df['skills'] = df['skills'].apply(lambda x: list(x) if hasattr(x, '__iter__') else [])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def main():
    """Main Streamlit app."""
    
    # Header
    st.markdown('<p class="main-header">💼 Job Market Intelligence Dashboard</p>', unsafe_allow_html=True)
    st.markdown("*Explore tech job market trends across Europe*")
    st.markdown("---")
    
    # Sidebar - File selection and filters
    st.sidebar.header("📁 Data Source")
    
    default_paths = [
        "data/curated/jobs_all_labeled.parquet",
        "data/curated/jobs_all_labeled_ml.parquet"
    ]
    
    available_files = [p for p in default_paths if Path(p).exists()]
    
    if not available_files:
        st.error("❌ No data files found! Please run the pipeline first:")
        st.code("python orchestration/run_pipeline.py --all")
        return
    
    selected_file = st.sidebar.selectbox(
        "Select Dataset",
        available_files,
        format_func=lambda x: "ML-Labeled" if "ml" in x else "Rule-Based"
    )
    
    # Load data
    df = load_data(selected_file)
    
    if df is None or len(df) == 0:
        st.error("Failed to load data or dataset is empty")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Country filter
    all_countries = sorted(df['country'].unique())
    selected_countries = st.sidebar.multiselect(
        "Countries",
        all_countries,
        default=all_countries
    )
    
    # Role filter
    all_roles = sorted(set([r for roles in df['roles'] for r in roles]))
    selected_roles = st.sidebar.multiselect(
        "Roles",
        all_roles,
        default=all_roles
    )
    
    # Salary filter
    has_salary = st.sidebar.checkbox("Only show jobs with salary", value=False)
    
    # Apply filters
    df_filtered = df[df['country'].isin(selected_countries)].copy()
    
    if selected_roles:
        df_filtered = df_filtered[df_filtered['roles'].apply(lambda x: any(r in selected_roles for r in x))]
    
    if has_salary:
        df_filtered = df_filtered[df_filtered['salary_min'].notna()]
    
    # Main content
    st.sidebar.markdown("---")
    st.sidebar.info(f"**Filtered Jobs**: {len(df_filtered):,} / {len(df):,}")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", f"{len(df_filtered):,}")
    
    with col2:
        st.metric("Countries", df_filtered['country'].nunique())
    
    with col3:
        salary_coverage = 100 * df_filtered['salary_min'].notna().sum() / len(df_filtered)
        st.metric("Salary Coverage", f"{salary_coverage:.1f}%")
    
    with col4:
        skills_coverage = 100 * df_filtered['skills'].apply(lambda x: len(x) > 0).sum() / len(df_filtered)
        st.metric("Skills Coverage", f"{skills_coverage:.1f}%")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Roles & Skills", "💰 Salaries", "🔬 ML vs Rules"])
    
    with tab1:
        st.markdown('<p class="sub-header">Dataset Overview</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Country Distribution")
            country_counts = df_filtered['country'].value_counts()
            st.bar_chart(country_counts)
        
        with col2:
            st.markdown("#### Jobs Over Time")
            if 'run_date' in df_filtered.columns:
                date_counts = df_filtered['run_date'].value_counts().sort_index()
                st.line_chart(date_counts)
        
        # Summary table
        st.markdown("#### Quick Stats")
        summary_df = pd.DataFrame({
            'Metric': ['Total Jobs', 'Unique Companies', 'With Salary', 'With Skills', 'Multi-Role Jobs'],
            'Value': [
                len(df_filtered),
                df_filtered['company'].nunique(),
                df_filtered['salary_min'].notna().sum(),
                df_filtered['skills'].apply(lambda x: len(x) > 0).sum(),
                df_filtered['roles'].apply(lambda x: len(x) > 1).sum()
            ]
        })
        st.dataframe(summary_df, width='stretch', hide_index=True)
    
    with tab2:
        st.markdown('<p class="sub-header">Roles & Skills Analysis</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Role Distribution")
            role_counts = Counter([r for roles in df_filtered['roles'] for r in roles])
            role_df = pd.DataFrame(role_counts.most_common(), columns=['Role', 'Count'])
            role_df['Role'] = role_df['Role'].str.replace('_', ' ').str.title()
            st.bar_chart(role_df.set_index('Role'))
            
            # Show table
            st.dataframe(role_df, width='stretch', hide_index=True)
        
        with col2:
            st.markdown("#### Top Skills")
            top_n = st.slider("Number of skills to show", 10, 50, 20)
            
            all_skills = [s for skills in df_filtered['skills'] for s in skills if len(skills) > 0]
            if all_skills:
                skill_counts = Counter(all_skills)
                skill_df = pd.DataFrame(skill_counts.most_common(top_n), columns=['Skill', 'Count'])
                st.bar_chart(skill_df.set_index('Skill'))
                
                with st.expander("View all skills"):
                    st.dataframe(skill_df, width='stretch', hide_index=True)
            else:
                st.info("No skills data available for filtered jobs")
    
    with tab3:
        st.markdown('<p class="sub-header">Salary Analysis</p>', unsafe_allow_html=True)
        
        df_salary = df_filtered[df_filtered['salary_min'].notna() & df_filtered['salary_max'].notna()].copy()
        
        if len(df_salary) > 0:
            df_salary['salary_mid'] = (df_salary['salary_min'] + df_salary['salary_max']) / 2
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Salary", f"€{df_salary['salary_mid'].mean():,.0f}")
            with col2:
                st.metric("Median Salary", f"€{df_salary['salary_mid'].median():,.0f}")
            with col3:
                st.metric("Jobs with Salary", len(df_salary))
            
            # Distribution
            st.markdown("#### Salary Distribution")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.hist(df_salary['salary_mid'], bins=30, color='#3b82f6', edgecolor='white')
            ax.set_xlabel('Salary (€)')
            ax.set_ylabel('Number of Jobs')
            ax.set_title('Salary Distribution')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            
            # By country
            st.markdown("#### Average Salary by Country")
            salary_by_country = df_salary.groupby('country')['salary_mid'].agg(['mean', 'count']).reset_index()
            salary_by_country = salary_by_country[salary_by_country['count'] >= 5]  # Filter small samples
            salary_by_country['country'] = salary_by_country['country'].str.upper()
            salary_by_country['mean'] = salary_by_country['mean'].round(0)
            
            st.bar_chart(salary_by_country.set_index('country')['mean'])
            st.dataframe(
                salary_by_country.rename(columns={'country': 'Country', 'mean': 'Avg Salary', 'count': 'Jobs'}),
                width='stretch',
                hide_index=True
            )
        else:
            st.info("No salary data available for filtered jobs")
    
    with tab4:
        st.markdown('<p class="sub-header">ML vs Rule-Based Classification</p>', unsafe_allow_html=True)
        
        # Check if both datasets exist
        ml_file = "data/curated/jobs_all_labeled_ml.parquet"
        rules_file = "data/curated/jobs_all_labeled.parquet"
        
        if Path(ml_file).exists() and Path(rules_file).exists():
            df_ml = load_data(ml_file)
            df_rules = load_data(rules_file)
            
            if df_ml is not None and df_rules is not None:
                # Random sample comparison
                st.markdown("#### Random Sample Comparison")
                
                n_samples = st.slider("Number of examples", 5, 20, 10)
                
                if st.button("Generate New Sample"):
                    st.rerun()
                
                sample_indices = random.sample(range(len(df_rules)), min(n_samples, len(df_rules)))
                
                for i, idx in enumerate(sample_indices, 1):
                    with st.expander(f"Example {i}: {df_rules.iloc[idx]['title'][:60]}..."):
                        job_rules = df_rules.iloc[idx]
                        job_ml = df_ml.iloc[idx]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Rule-Based**")
                            roles_rules = [r.replace('_', ' ').title() for r in job_rules['roles']]
                            st.write("Roles:", ", ".join(roles_rules))
                        
                        with col2:
                            st.markdown("**ML-Based**")
                            roles_ml = [r.replace('_', ' ').title() for r in job_ml['roles']]
                            st.write("Roles:", ", ".join(roles_ml))
                        
                        # Highlight differences
                        set_rules = set(job_rules['roles'])
                        set_ml = set(job_ml['roles'])
                        
                        if set_rules != set_ml:
                            added = set_ml - set_rules
                            removed = set_rules - set_ml
                            
                            if added:
                                st.success(f"✅ ML added: {', '.join([r.replace('_', ' ').title() for r in added])}")
                            if removed:
                                st.warning(f"⚠️ ML removed: {', '.join([r.replace('_', ' ').title() for r in removed])}")
                        else:
                            st.info("✓ Perfect agreement")
                        
                        # Show job details
                        with st.expander("Job Details"):
                            st.write(f"**Country**: {job_rules['country'].upper()}")
                            st.write(f"**Company**: {job_rules['company']}")
                            if len(job_rules['skills']) > 0:
                                st.write(f"**Skills**: {', '.join(job_rules['skills'][:10])}")
                            if pd.notna(job_rules['salary_min']):
                                st.write(f"**Salary**: €{job_rules['salary_min']:,.0f} - €{job_rules['salary_max']:,.0f}")
                
                # Overall comparison stats
                st.markdown("---")
                st.markdown("#### Overall Comparison")
                
                df_rules['roles_str'] = df_rules['roles'].apply(lambda x: ','.join(sorted(x)))
                df_ml['roles_str'] = df_ml['roles'].apply(lambda x: ','.join(sorted(x)))
                
                agreement = (df_rules['roles_str'] == df_ml['roles_str']).sum()
                agreement_pct = 100 * agreement / len(df_rules)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Agreement", f"{agreement_pct:.1f}%")
                with col2:
                    st.metric("Agreements", f"{agreement:,}")
                with col3:
                    st.metric("Disagreements", f"{len(df_rules) - agreement:,}")
                
            else:
                st.error("Failed to load comparison datasets")
        else:
            st.info("""
            ML comparison not available. To enable:
            1. Run pipeline with rule-based classification: `python orchestration/run_pipeline.py --label`
            2. Train ML model: `python orchestration/run_pipeline.py --train-role-model`
            3. Run pipeline with ML classification: `python orchestration/run_pipeline.py --label --ml`
            """)
    
    # Data table at the bottom
    st.markdown("---")
    st.markdown('<p class="sub-header">📋 Job Listings</p>', unsafe_allow_html=True)
    
    # Prepare display dataframe
    display_df = df_filtered[[
        'title', 'country', 'company', 'roles', 'skills', 'salary_min', 'salary_max'
    ]].copy()
    
    display_df['roles'] = display_df['roles'].apply(lambda x: ', '.join([r.replace('_', ' ').title() for r in x]))
    display_df['skills'] = display_df['skills'].apply(lambda x: ', '.join(x[:5]) + ('...' if len(x) > 5 else ''))
    display_df['country'] = display_df['country'].str.upper()
    display_df.columns = ['Title', 'Country', 'Company', 'Roles', 'Skills', 'Salary Min', 'Salary Max']
    
    st.dataframe(
        display_df.head(100),
        width='stretch',
        hide_index=True,
        height=400
    )
    
    st.caption(f"Showing first 100 of {len(df_filtered):,} jobs")
    
    # Footer
    st.markdown("---")
    st.markdown("*Job Market Intelligence Dashboard • Data Science & ML Jobs Across Europe*")


if __name__ == '__main__':
    main()
