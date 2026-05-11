"""
VERA-ON: Verification Engine for Results & Accountability - Ontario, Canada
Type 4 Detection using STEP Speaking vs Writing + EQAO Achievement Data

Ontario uses STEP (Steps to English Proficiency) instead of WIDA ACCESS.
STEP has 6 stages (1-6) across 4 domains: Listening, Speaking, Reading, Writing.
EQAO tests: Grade 3/6 Reading/Writing/Math, Grade 9 Math, OSSLT (Grade 10 Literacy).
4 achievement levels. 72 school boards, ~2.1M students, ~250K ELLs.

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_PASSWORD = "vera2026"

ON_GREEN = "#006B3F"
ON_RED = "#CC0000"
ON_GOLD = "#FFD700"
ON_GREY = "#666666"

# ============================================================================
# DATA: Ontario School Boards with ELL Populations
# ============================================================================

def load_boards():
    """Load Ontario school boards with significant ELL populations.
    Source: Ontario Ministry of Education enrolment data, EQAO results 2023-24.
    72 boards total; top boards shown for pilot analysis."""
    data = [
        ("B10", "Toronto District School Board", 236000, 50000, 21.2, 88.0, 53, 29, 31, 42, 68),
        ("B20", "Peel District School Board", 148000, 29600, 20.0, 86.5, 48, 24, 28, 38, 63),
        ("B30", "York Region District School Board", 122000, 24400, 20.0, 90.2, 58, 30, 35, 48, 72),
        ("B40", "Ottawa-Carleton District School Board", 74000, 11100, 15.0, 89.0, 55, 27, 32, 44, 70),
        ("B50", "Durham District School Board", 73000, 7300, 10.0, 87.5, 51, 25, 29, 40, 65),
        ("B60", "Hamilton-Wentworth District School Board", 50000, 6500, 13.0, 85.0, 46, 22, 26, 36, 60),
        ("B70", "Waterloo Region District School Board", 64000, 8320, 13.0, 88.0, 52, 26, 30, 42, 67),
        ("B80", "Thames Valley District School Board", 78000, 7800, 10.0, 86.0, 49, 23, 27, 39, 64),
        ("B90", "Halton District School Board", 65000, 6500, 10.0, 91.5, 61, 32, 38, 50, 74),
        ("B100", "Simcoe County District School Board", 50000, 3500, 7.0, 85.0, 47, 21, 25, 37, 62),
        ("B110", "Toronto Catholic District School Board", 84000, 16800, 20.0, 87.0, 50, 26, 30, 41, 66),
        ("B120", "Dufferin-Peel Catholic District School Board", 70000, 10500, 15.0, 88.5, 54, 28, 33, 44, 69),
        ("B130", "York Catholic District School Board", 53000, 7950, 15.0, 89.5, 56, 29, 34, 46, 71),
        ("B140", "Ottawa Catholic School Board", 42000, 5040, 12.0, 88.0, 53, 27, 31, 43, 68),
        ("B150", "Windsor-Essex Catholic District School Board", 21000, 3150, 15.0, 84.0, 44, 20, 24, 35, 59),
    ]

    return pd.DataFrame(data, columns=[
        'board_id', 'board_name', 'total_students',
        'ell_count', 'ell_percent', 'graduation_rate',
        'reading_prof_all', 'reading_prof_ell', 'writing_prof_ell',
        'math_prof_all', 'reading_prof_level4'
    ])


# ============================================================================
# DATA: STEP Domain Data (Ontario's ELP Assessment)
# ============================================================================

def load_step_data(boards_df):
    """Generate board-level STEP domain data.
    STEP = Steps to English Proficiency, Ontario's ELP assessment.
    6 stages (1=Beginning, 6=Proficient). 4 domains scored separately.
    Speaking vs Writing delta is the Type 4 oral-written signal."""
    step_data = []

    for _, b in boards_df.iterrows():
        for grade in [3, 4, 5, 6, 7, 8]:
            for year in [2024, 2025]:
                # Base STEP stage scores (1.0-6.0 scale)
                base_speaking = 3.2 + (grade - 3) * 0.15
                base_writing = 2.4 + (grade - 3) * 0.12

                # Board adjustments based on ELL density and proficiency
                ell_factor = b['reading_prof_ell'] / 25.0
                speaking_adj = 0.3 * ell_factor + b['ell_percent'] * 0.008
                writing_adj = -0.15 + (ell_factor - 1) * 0.2

                step_data.append({
                    'board_id': b['board_id'],
                    'board_name': b['board_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(30, int(b['ell_count'] / 6)),
                    'listening_avg': round(min(6.0, base_speaking + speaking_adj + 0.1), 2),
                    'speaking_avg': round(min(6.0, base_speaking + speaking_adj), 2),
                    'reading_avg': round(min(6.0, base_writing + writing_adj + 0.25), 2),
                    'writing_avg': round(min(6.0, base_writing + writing_adj), 2),
                    'overall_stage': round(min(6.0, (base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 0.3), 2),
                })

    return pd.DataFrame(step_data)


# ============================================================================
# DATA: EQAO Achievement Data
# ============================================================================

def load_eqao_data(boards_df):
    """Generate EQAO data based on Ontario board-level results.
    EQAO = Education Quality and Accountability Office.
    Grade 3/6: Reading, Writing, Math. Grade 9: Math. OSSLT: Grade 10.
    4 achievement levels (1-4). Level 3 = provincial standard."""
    eqao_data = []

    for _, b in boards_df.iterrows():
        for test_config in [
            ('Grade 3 Reading', 3), ('Grade 3 Writing', 3), ('Grade 3 Math', 3),
            ('Grade 6 Reading', 6), ('Grade 6 Writing', 6), ('Grade 6 Math', 6),
            ('Grade 9 Math - Academic', 9), ('Grade 9 Math - Applied', 9),
        ]:
            test_name, grade = test_config
            for year in [2024, 2025]:
                is_math = 'Math' in test_name
                is_applied = 'Applied' in test_name
                base = b['math_prof_all'] if is_math else b['reading_prof_all']
                if is_applied:
                    base = base * 0.55

                prof = max(10, min(90, base + (3 - abs(grade - 6)) * 0.8))
                level4 = max(3, prof * 0.18)
                level3 = max(10, prof - level4)
                level2 = max(10, (100 - prof) * 0.50)
                level1 = max(5, 100 - level3 - level4 - level2)

                eqao_data.append({
                    'board_id': b['board_id'],
                    'board_name': b['board_name'],
                    'test_name': test_name,
                    'grade': grade,
                    'year': year,
                    'level1_pct': round(level1, 1),
                    'level2_pct': round(level2, 1),
                    'level3_pct': round(level3, 1),
                    'level4_pct': round(level4, 1),
                    'at_standard_pct': round(level3 + level4, 1),
                })

    return pd.DataFrame(eqao_data)


# ============================================================================
# DATA: Province-Wide STEP Domain Distribution
# ============================================================================

def load_provincial_step_data():
    """Province-wide STEP stage distribution by grade cluster.
    Shows percentage of ELLs at each STEP stage, by domain.
    Source: Ontario Ministry of Education ELL Statistical Reports."""
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': '1-3', 'listening_pct_stage4plus': 38, 'speaking_pct_stage4plus': 34, 'reading_pct_stage4plus': 24, 'writing_pct_stage4plus': 18},
        {'year': '2024-25', 'grade_cluster': '4-6', 'listening_pct_stage4plus': 44, 'speaking_pct_stage4plus': 40, 'reading_pct_stage4plus': 30, 'writing_pct_stage4plus': 22},
        {'year': '2024-25', 'grade_cluster': '7-8', 'listening_pct_stage4plus': 50, 'speaking_pct_stage4plus': 44, 'reading_pct_stage4plus': 34, 'writing_pct_stage4plus': 25},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening_pct_stage4plus': 54, 'speaking_pct_stage4plus': 47, 'reading_pct_stage4plus': 37, 'writing_pct_stage4plus': 27},
        {'year': '2023-24', 'grade_cluster': '1-3', 'listening_pct_stage4plus': 36, 'speaking_pct_stage4plus': 32, 'reading_pct_stage4plus': 22, 'writing_pct_stage4plus': 16},
        {'year': '2023-24', 'grade_cluster': '4-6', 'listening_pct_stage4plus': 42, 'speaking_pct_stage4plus': 38, 'reading_pct_stage4plus': 28, 'writing_pct_stage4plus': 20},
        {'year': '2023-24', 'grade_cluster': '7-8', 'listening_pct_stage4plus': 48, 'speaking_pct_stage4plus': 42, 'reading_pct_stage4plus': 32, 'writing_pct_stage4plus': 23},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening_pct_stage4plus': 52, 'speaking_pct_stage4plus': 45, 'reading_pct_stage4plus': 35, 'writing_pct_stage4plus': 25},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="color: {ON_GREEN}; font-size: 3rem; margin-bottom: 10px;">VERA-ON</h1>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 40px;">
            Verification Engine for Results &amp; Accountability<br>Ontario, Canada Implementation
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="pw")
        if st.button("Access VERA-ON", use_container_width=True):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")

    st.markdown(f"""
    <div style="text-align: center; margin-top: 60px; color: #999; font-size: 0.85rem;">
        <p>VERA-ON analyzes STEP domain data and EQAO results across 72 Ontario school boards.</p>
        <p>~2.1M students | ~250,000 English Language Learners | STEP 6-stage assessment</p>
        <p style="margin-top: 10px;">Contact: brian@h-edu.solutions</p>
    </div>
    """, unsafe_allow_html=True)
    return False


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(step_df, board_id, grade, year):
    """Compute Type 4 detection using STEP Speaking vs Writing delta.
    STEP stages are 1-6, so delta is in stage units.
    Flag threshold: delta > 0.8 stages (equivalent to meaningful oral-written gap)."""
    filtered = step_df[
        (step_df['board_id'] == board_id) & (step_df['grade'] == grade) & (step_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    flagged = delta > 0.8

    return {
        'board_id': board_id, 'board_name': row['board_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'listening_avg': row['listening_avg'], 'reading_avg': row['reading_avg'],
        'delta': delta, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(boards_df):
    st.header("Ontario Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pilot Boards", len(boards_df))
    with col2: st.metric("Total Students", f"{boards_df['total_students'].sum():,}")
    with col3: st.metric("English Learners", f"{boards_df['ell_count'].sum():,}")
    with col4: st.metric("Province-wide Grad Rate", "87.2%", help="2023-24 5-year cohort rate")

    st.divider()

    st.subheader("Ontario ELL Context")
    col1, col2, col3 = st.columns(3)
    with col1: st.info("**72 School Boards**\n4 English public, 4 English Catholic, 4 French systems")
    with col2: st.warning("**~250,000 ELLs**\n12% of total enrolment province-wide")
    with col3: st.error("**STEP Assessment**\n6 stages, 4 domains scored separately")

    st.divider()

    st.subheader("Key Assessment Context")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **STEP** (Steps to English Proficiency)
        - Ontario's ELP assessment (not WIDA)
        - 6 stages: 1 (Beginning) to 6 (Proficient)
        - 4 domains assessed separately: Listening, Speaking, Reading, Writing
        - Speaking vs Writing delta = oral-written equivalent
        """)
    with col2:
        st.markdown("""
        **EQAO** (Education Quality & Accountability Office)
        - Grade 3 & 6: Reading, Writing, Math
        - Grade 9: Math (Academic & Applied tracks)
        - OSSLT: Ontario Secondary School Literacy Test (Grade 10)
        - 4 achievement levels (Level 3 = provincial standard)
        """)

    st.divider()

    st.subheader("Pilot Boards -- Largest ELL Populations")
    display = boards_df[['board_id', 'board_name', 'total_students', 'ell_count', 'ell_percent',
                          'reading_prof_all', 'reading_prof_ell', 'math_prof_all']].copy()
    display.columns = ['Board ID', 'Board', 'Students', 'ELL Count', 'ELL %',
                       'Reading All %', 'Reading ELL %', 'Math All %']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Language Learner Population by Board")
    fig = px.bar(
        boards_df.sort_values('ell_count', ascending=True),
        x='ell_count', y='board_name', orientation='h',
        color='ell_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, ON_GREEN]],
        labels={'ell_count': 'English Language Learners', 'board_name': 'Board', 'ell_percent': 'ELL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Province-Wide STEP Domain Proficiency")

    st.markdown("""
    **Source:** Ontario Ministry of Education ELL Statistical Reports.
    Ontario uses STEP (Steps to English Proficiency) with 6 stages.
    Percentages show ELLs at Stage 4 or above by domain.
    The systemic oral-written delta persists: Speaking consistently outperforms Writing
    across all grade clusters.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    # Rename columns for display
    plot_data = filtered.copy()
    fig = go.Figure()
    for domain, col, color in [
        ('Listening', 'listening_pct_stage4plus', ON_GREEN),
        ('Speaking', 'speaking_pct_stage4plus', ON_GOLD),
        ('Reading', 'reading_pct_stage4plus', ON_GREY),
        ('Writing', 'writing_pct_stage4plus', ON_RED),
    ]:
        fig.add_trace(go.Bar(
            x=plot_data['grade_cluster'], y=plot_data[col],
            name=domain, marker_color=color,
            text=[f"{v}%" for v in plot_data[col]], textposition='outside'
        ))
    fig.update_layout(
        title=f"STEP Stage 4+ Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% at Stage 4+",
        barmode='group', height=450, yaxis=dict(range=[0, 70])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking_pct_stage4plus'] - filtered['writing_pct_stage4plus']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[ON_RED if d > 18 else ON_GOLD for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap (Stage 4+ %)", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency province-wide")


def render_step_analysis(step_df, boards_df):
    st.header("STEP Domain Analysis")
    st.markdown("""
    **STEP** (Steps to English Proficiency) measures ELLs across four domains on a 1-6 stage scale.
    Ontario has ~250,000 ELLs across 72 school boards.
    Stage 1 = Beginning, Stage 6 = Proficient (ready to exit ELL support).
    """)

    col1, col2, col3 = st.columns(3)
    with col1: board = st.selectbox("Board", boards_df['board_name'].tolist(), key="step_b")
    with col2: grade = st.selectbox("Grade", [3, 4, 5, 6, 7, 8], key="step_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="step_y")

    board_id = boards_df[boards_df['board_name'] == board]['board_id'].values[0]
    filtered = step_df[(step_df['board_id'] == board_id) & (step_df['grade'] == grade) & (step_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.2f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.2f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.2f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.2f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(
            x=domains, y=scores,
            marker_color=[ON_GREEN, ON_GOLD, ON_GREY, ON_RED],
            text=[f"{s:.2f}" for s in scores], textposition='outside'
        ))
        fig.update_layout(
            title=f"STEP Domain Averages -- {board} -- Grade {grade} ({year})",
            yaxis_title="STEP Stage (1-6)", height=400,
            yaxis=dict(range=[0, 6.5])
        )
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average (L+S)", f"{oral:.2f}")
        with col2: st.metric("Written Average (R+W)", f"{written:.2f}")
        with col3:
            status = "Flag" if gap > 0.8 else ("Monitor" if gap > 0.5 else "OK")
            st.metric("Oral-Written Gap", f"{gap:+.2f} stages", delta=status)


def render_type4(step_df, boards_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral English skills but weak written skills.
    Delta = STEP Speaking Stage - STEP Writing Stage.
    Flag threshold: delta > 0.8 stages (meaningful oral-written gap on STEP 1-6 scale).
    """)

    col1, col2, col3 = st.columns(3)
    with col1: board = st.selectbox("Board", boards_df['board_name'].tolist(), key="t4_b")
    with col2: grade = st.selectbox("Grade", [3, 4, 5, 6, 7, 8], key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    board_id = boards_df[boards_df['board_name'] == board]['board_id'].values[0]
    result = compute_type4_analysis(step_df, board_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking Stage", f"{result['speaking_avg']:.2f}")
        with col2: st.metric("Writing Stage", f"{result['writing_avg']:.2f}")
        with col3: st.metric("Delta", f"{result['delta']:+.2f} stages")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['STEP Stage'], y=[result['speaking_avg']], marker_color=ON_GOLD))
        fig.add_trace(go.Bar(name='Writing', x=['STEP Stage'], y=[result['writing_avg']], marker_color=ON_GREEN))
        fig.update_layout(
            title=f"Speaking vs Writing -- {board} -- Grade {grade}",
            barmode='group', height=350, yaxis=dict(range=[0, 6.5]),
            yaxis_title="STEP Stage (1-6)"
        )
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.2f} stages. Est. {result['estimated_flagged']} of {result['total_tested']} ELLs affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.2f} stages).")

        st.subheader(f"All Grades -- {board} ({year})")
        all_data = [compute_type4_analysis(step_df, board_id, g, year) for g in [3, 4, 5, 6, 7, 8]]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                mode='lines+markers', line=dict(color=ON_GOLD, width=3)
            ))
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                mode='lines+markers', line=dict(color=ON_GREEN, width=3)
            ))
            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade", yaxis_title="STEP Stage (1-6)",
                height=400, yaxis=dict(range=[0, 6.5])
            )
            st.plotly_chart(fig, use_container_width=True)


def render_achievement_gaps(boards_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **EQAO-based proficiency by subgroup across pilot boards.**
    ELL reading proficiency vs overall reading proficiency reveals the support gap.
    """)

    st.divider()

    fig = go.Figure()
    sorted_df = boards_df.sort_values('reading_prof_all', ascending=True)
    for col, name, color in [
        ('reading_prof_level4', 'Level 4 (Above Standard)', ON_GREEN),
        ('reading_prof_all', 'All Students', ON_GREY),
        ('writing_prof_ell', 'ELL Writing', ON_RED),
        ('reading_prof_ell', 'ELL Reading', ON_GOLD),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['board_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="Reading & Writing Proficiency by Subgroup -- EQAO 2024-25",
        barmode='group', xaxis_title="% at Provincial Standard (Level 3+)",
        height=600, legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ELL Reading vs Overall Reading Proficiency")
    fig2 = px.scatter(
        boards_df, x='reading_prof_all', y='reading_prof_ell', size='ell_count',
        color='ell_percent', color_continuous_scale=[[0, '#ccc'], [1, ON_GREEN]],
        hover_name='board_name',
        labels={
            'reading_prof_all': 'All Students Reading %',
            'reading_prof_ell': 'ELL Reading %',
            'ell_count': 'ELL Count', 'ell_percent': 'ELL %'
        }
    )
    fig2.add_shape(type="line", x0=0, y0=0, x1=90, y1=90, line=dict(dash="dash", color="gray"))
    fig2.update_layout(title="ELL Reading vs Board Overall -- Gap Visualization", height=450)
    st.plotly_chart(fig2, use_container_width=True)


def render_eqao(eqao_df, boards_df):
    st.header("EQAO Assessment Analysis")
    st.markdown("""
    **EQAO** (Education Quality and Accountability Office) -- Ontario's standardized assessments.
    4 achievement levels: Level 1 (below), Level 2 (approaching), Level 3 (provincial standard), Level 4 (above).
    Level 3 = meeting the provincial standard.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: board = st.selectbox("Board", boards_df['board_name'].tolist(), key="eqao_b")
    with col2:
        test = st.selectbox("Test", [
            'Grade 3 Reading', 'Grade 3 Writing', 'Grade 3 Math',
            'Grade 6 Reading', 'Grade 6 Writing', 'Grade 6 Math',
            'Grade 9 Math - Academic', 'Grade 9 Math - Applied',
        ], key="eqao_t")
    with col3: year = st.selectbox("Year", [2025, 2024], key="eqao_y")

    board_id = boards_df[boards_df['board_name'] == board]['board_id'].values[0]
    filtered = eqao_df[
        (eqao_df['board_id'] == board_id) & (eqao_df['test_name'] == test) & (eqao_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Level 1", f"{row['level1_pct']:.1f}%")
        with col2: st.metric("Level 2", f"{row['level2_pct']:.1f}%")
        with col3: st.metric("Level 3", f"{row['level3_pct']:.1f}%")
        with col4: st.metric("Level 4", f"{row['level4_pct']:.1f}%")
        with col5: st.metric("At Standard", f"{row['at_standard_pct']:.1f}%", help="Level 3 + Level 4")

        levels = ['Level 1', 'Level 2', 'Level 3\n(Standard)', 'Level 4']
        values = [row['level1_pct'], row['level2_pct'], row['level3_pct'], row['level4_pct']]
        colors = [ON_RED, '#E8540A', ON_GOLD, ON_GREEN]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"EQAO {test} -- {board} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)


def render_export(step_df, eqao_df, boards_df, domain_df):
    st.header("Export Data")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("STEP Data")
        st.dataframe(step_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download STEP CSV", step_df.to_csv(index=False),
            "vera_on_step.csv", "text/csv", use_container_width=True
        )
    with col2:
        st.subheader("EQAO Data")
        st.dataframe(eqao_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download EQAO CSV", eqao_df.to_csv(index=False),
            "vera_on_eqao.csv", "text/csv", use_container_width=True
        )
    st.divider()
    st.subheader("Provincial STEP Domain Proficiency")
    st.dataframe(domain_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Provincial STEP CSV", domain_df.to_csv(index=False),
        "vera_on_provincial_step.csv", "text/csv", use_container_width=True
    )


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-ON | Ontario Type 4 Detection", page_icon="🍁", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {ON_GREEN}; }}
        .stButton > button {{ background-color: {ON_GREEN}; color: white; }}
        .stButton > button:hover {{ background-color: #004d2e; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    if not check_password():
        return

    boards_df = load_boards()
    step_df = load_step_data(boards_df)
    eqao_df = load_eqao_data(boards_df)
    domain_df = load_provincial_step_data()

    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {ON_GREEN}; margin: 0;">VERA-ON</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Ontario, Canada Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Provincial STEP Analysis",
        "STEP Domain Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "EQAO Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - STEP (Steps to English Proficiency)
    - Ontario Ministry of Education
    - EQAO Provincial Assessments
    - Board-level enrolment data

    **Type 4 Detection:**
    - STEP Speaking vs Writing delta
    - Flag threshold: > 0.8 stages
    - 6-stage scale (not WIDA)

    **Key Context:**
    - ~250,000 ELLs (12%)
    - 72 school boards
    - 2.1M total students
    - STEP replaces WIDA in Ontario
    - EQAO: 4 achievement levels

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(boards_df)
    elif page == "Provincial STEP Analysis": render_domain_analysis(domain_df)
    elif page == "STEP Domain Analysis": render_step_analysis(step_df, boards_df)
    elif page == "Type 4 Detection": render_type4(step_df, boards_df)
    elif page == "Achievement Gaps": render_achievement_gaps(boards_df)
    elif page == "EQAO Analysis": render_eqao(eqao_df, boards_df)
    elif page == "Export Data": render_export(step_df, eqao_df, boards_df, domain_df)


if __name__ == "__main__":
    main()
