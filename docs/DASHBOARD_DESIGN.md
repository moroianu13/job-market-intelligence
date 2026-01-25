# Job Market Intelligence Dashboard — Design & Architecture

## Overview

A professional, production-grade Streamlit dashboard refactored from a "demo" UI into an analytics tool suitable for Computer Science professionals, technical recruiters, and ML engineers.

---

## 🎨 Visual Design Principles

### Color Palette

| Use | Color | Value |
|-----|-------|-------|
| Primary (Headers, Accent) | Professional Blue | `#2E5090` |
| Secondary (Charts) | Lighter Blue | `#547DBF` |
| Success State | Professional Green | `#10A37F` |
| Warning/Changed | Professional Amber | `#D97706` |
| Neutral (Text, Labels) | Gray | `#6B7280` |

**Rationale**: Neutral blue/gray palette signals "professional analytics tool" rather than "fun demo." No bright colors, no rainbow gradients.

### Typography

- **Page Title**: 2.2rem, 700 weight, letter-spaced — establishes authority
- **Section Headers**: 1.3rem, 600 weight — clear hierarchy without emojis
- **Labels**: 0.85rem, 600 weight, uppercase, letter-spaced — high contrast, scannable

### No Emojis

Removed all emoji from headers, tabs, and UI elements:
- ❌ `"💼 Job Market Intelligence Dashboard"` → ✅ `"Job Market Intelligence"`
- ❌ `"📊 Overview"` → ✅ `"Overview"`
- ❌ `"💰 Salaries"` → ✅ `"Compensation"`
- Page icon changed from `💼` to `▲` (professional, minimal)

---

## 📐 Layout & Architecture

### Sidebar Structure

**Fixed, sticky navigation** containing:

1. **Data Source** selector
   - Rule-Based vs Machine Learning
   - Loads appropriate parquet file

2. **Filters** section
   - Countries (multi-select, default all)
   - Roles (multi-select, default empty)
   - Salary data toggle

3. **Filter Summary**
   - Shows filtered count vs total
   - Displays active filter state

**UX Decision**: Filters remain visible while scrolling, reducing cognitive load.

### Main Content Tabs

| Tab | Purpose | Components |
|-----|---------|------------|
| **Overview** | Dataset summary & trends | Country distribution, timeline, summary stats |
| **Roles & Skills** | Role/skill demand analysis | Top roles, top skills, skill count slider |
| **Compensation** | Salary insights & distribution | Avg/median/min/max metrics, histogram, by-country breakdown |
| **Methods** | ML vs Rule-based comparison | Agreement %, sample diffs, classification explanation |
| **Job Listings** | Paginated job table | Searchable, sortable, 10/25/50/100 rows per page |

**No emoji in tab labels** — clarity through naming, not decoration.

---

## 📊 Data Visualization Improvements

### Replaced: Streamlit's Default Charts

| Old | New | Benefit |
|-----|-----|---------|
| `st.bar_chart()` | Plotly `px.bar()` | Titles, axis labels, hover details, proper sizing |
| `st.line_chart()` | Plotly `px.line()` with markers | Professional styling, consistent interaction |
| matplotlib histograms | Plotly `px.histogram()` | Unified styling, better UX |

### Chart Design Standards

Every chart includes:

1. **Title**: Clear, descriptive (e.g., "Country Distribution")
2. **Axis Labels**: Explicit (e.g., "Salary (€)", "Number of Jobs")
3. **Subtitle/Caption**: Short explanation below chart
4. **Consistent Color**: 1–2 colors per chart (primary/secondary blue)
5. **Grid**: Subtle background gridlines for readability
6. **Hover Details**: Plotly's built-in interactivity for exploration

### Example: Country Distribution Chart

```python
fig = px.bar(
    x=country_counts.index.str.upper(),
    y=country_counts.values,
    labels={'x': '', 'y': 'Number of Jobs'},
    color_discrete_sequence=[COLOR_PRIMARY],
    height=400
)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')
st.plotly_chart(fig, use_container_width=True)
st.caption("Top 15 countries by job count")
```

---

## 🎯 KPI Cards

Replaced default `st.metric()` with custom styled cards for better visual control:

```html
<div class="kpi-card">
    <div class="kpi-value">1,234</div>
    <div class="kpi-label">Total Jobs</div>
</div>
```

**Features**:
- Gradient background (light gray to darker gray)
- Left border accent (primary blue)
- Large number, small uppercase label
- Consistent height & spacing
- Dark mode aware (CSS media query)

---

## 📋 Job Table (Pagination)

**Key improvements over `.head(100)` dump**:

1. **Page Size Selector**: Choose 10, 25, 50, or 100 rows per page
2. **Page Indicator**: "Page 1 of 42 (showing 25 of 1,234 jobs)"
3. **Columns Shown**:
   - Title
   - Country (uppercase for scannability)
   - Company
   - Roles (formatted, comma-separated)
   - Skills (first 4 with "..." truncation)
   - Salary Range (€X – €Y format, or "—" if missing)

4. **Interactive Height**: 500px table with scrolling
5. **Smart Truncation**: Skills limited to 4 visible items with expansion hint

**Feels like**: Real job monitoring tool, not a dataframe dump.

---

## 🤖 ML vs Rule-Based Tab

**Reframed from random demo to structured comparison**:

### Section 1: Overview Metrics
- Overall Agreement % (large, prominent)
- Agreed count
- Disagreement count
- Total records

### Section 2: Methodology Explanation
```
Rule-Based: Pattern matching on job text (fast, transparent)
ML Model: Gradient boosting trained on hand-labeled samples (flexible)
```

### Section 3: Sample Differences
- Shows only disagreements (not random samples)
- Each expandable example shows:
  - Job title + country
  - Side-by-side role outputs (Rule-Based vs ML)
  - Green highlight: "ML added..."
  - Red highlight: "ML removed..."
  - Expandable context (company, salary, skills)

**Rationale**: Engineers want to understand *why* classifiers differ, not just see random examples.

---

## 🧼 Code Quality & Modularization

### Function Breakdown

Each UI section is a modular function with docstrings:

```python
def render_kpi_cards(df: pd.DataFrame) -> None:
    """Render KPI metric cards in a 4-column grid."""

def render_overview(df: pd.DataFrame) -> None:
    """Render Overview tab with country distribution, timeline, and summary stats."""

def render_roles_skills(df: pd.DataFrame) -> None:
    """Render Roles & Skills analysis with distributions and top skills."""

def render_salaries(df: pd.DataFrame) -> None:
    """Render salary analysis with distribution, statistics, and by-country breakdown."""

def render_ml_comparison(df_rules: pd.DataFrame, df_ml: pd.DataFrame) -> None:
    """Render ML vs Rule-based classification comparison."""

def render_job_table(df: pd.DataFrame) -> None:
    """Render paginated job listings table."""

def render_about() -> None:
    """Render footer with system information and methodology."""
```

**Benefits**:
- Easy to test, modify, reorder
- Self-documenting (docstrings explain purpose)
- Reusable across different dashboards
- Clear separation of concerns

---

## 🌙 Dark Mode Support

CSS includes `@media (prefers-color-scheme: dark)` queries:

```css
@media (prefers-color-scheme: dark) {
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    }
    .kpi-value {
        color: #547DBF;  /* Lighter blue for contrast on dark background */
    }
}
```

Works with system preferences and Streamlit's built-in dark mode.

---

## ℹ️ About Section (Footer)

Three-column layout explaining the system:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| **Data Pipeline** | **Classification Methods** | **Key Features** |
| • Scrapes Adzuna | • Rule-Based (fast) | • Ghost job detection |
| • Normalizes data | • ML Model (flexible) | • Multi-role IDs |
| • Extracts metadata | • Updated weekly | • Salary normalization |
| • Detects reposts | | • Skills extraction |

**Audience**: Anyone asking "where does this data come from?"

---

## 🔧 Technical Decisions

### Why Plotly over Matplotlib?

1. **Consistent UX**: Hover, zoom, pan work across all charts
2. **Styling**: Easy to control colors, fonts, gridlines
3. **Responsive**: Automatically scales to container width
4. **Interactive**: Built-in legend toggle, export as PNG
5. **Professional**: Matches SaaS product standards

### Why Custom CSS over st.metric()?

`st.metric()` doesn't allow fine control over styling. Custom HTML + CSS enables:
- Gradient backgrounds
- Left border accents
- Typography fine-tuning
- Dark mode awareness

### Filter State Management

Filters remain in sidebar (not global state) because:
- Reduces cognitive load
- Clear visual hierarchy (controls on left, content on right)
- Aligns with standard SaaS dashboard UX (Grafana, Looker, Tableau)

---

## 📦 Dependencies Added

```bash
plotly>=5.14.0
```

Added to both `requirements.txt` and `requirements-streamlit.txt` for consistency.

---

## 🚀 Performance Considerations

1. **@st.cache_data**: Data loading cached to avoid re-reading parquet
2. **Lazy Tabs**: Tab content only renders when clicked
3. **Plotly Height**: Charts render at fixed heights (no layout thrashing)
4. **DataFrame Filtering**: Efficient boolean masking (no `.apply()` on large ops)

---

## 🎯 Result

The dashboard now communicates:

> *"This is a professional ML-powered job market intelligence system built by a data/ML engineer."*

Not:

> *"Streamlit demo with cool features."*

**Visual signals**:
- ✅ No emoji
- ✅ Professional blue/gray palette
- ✅ Clear typography hierarchy
- ✅ Plotly charts with labels & subtitles
- ✅ Sticky sidebar with smart filters
- ✅ Modular, documented code
- ✅ Pagination on tables
- ✅ Dark mode support
- ✅ Methodology explanations

Suitable for portfolio demos, internal analytics, and technical interviews.
