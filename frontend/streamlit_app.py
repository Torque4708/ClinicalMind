"""
ClinicalMind — Streamlit Frontend
Multi-page AI Clinical Trial Intelligence & Patient Matching App
"""
import os
import json
import streamlit as st
import requests
import pandas as pd
from typing import Optional

# ── Config ─────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="ClinicalMind",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Defaults ──────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Helper Functions ────────────────────────────────────────────────────────

def auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_get(path: str, params: dict = None) -> Optional[requests.Response]:
    try:
        resp = requests.get(f"{BACKEND_URL}{path}", headers=auth_headers(), params=params, timeout=30)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the ClinicalMind backend. Make sure it is running.")
        return None


def api_post(path: str, payload: dict) -> Optional[requests.Response]:
    try:
        resp = requests.post(
            f"{BACKEND_URL}{path}",
            json=payload,
            headers=auth_headers(),
            timeout=60,
        )
        return resp
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the ClinicalMind backend. Make sure it is running.")
        return None


def is_logged_in() -> bool:
    return st.session_state.token is not None


def logout():
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.chat_history = []
    st.rerun()


# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #e0e0e0;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #a0aec0;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    .trial-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
        border: 1px solid rgba(102,126,234,0.3);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.1rem;
    }
    .badge-recruiting {
        background: rgba(72,199,142,0.2);
        color: #48c78e;
        border: 1px solid #48c78e;
    }
    .badge-phase {
        background: rgba(102,126,234,0.2);
        color: #667eea;
        border: 1px solid #667eea;
    }
    .chat-message-user {
        background: rgba(102,126,234,0.2);
        border-radius: 12px 12px 2px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        text-align: right;
    }
    .chat-message-ai {
        background: rgba(255,255,255,0.07);
        border-radius: 12px 12px 12px 2px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }
    div[data-testid="stSidebar"] {
        background: rgba(15,12,41,0.9);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(102,126,234,0.4);
    }
    .metric-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar Navigation ──────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🧬 ClinicalMind")
        st.markdown("*AI Clinical Trial Intelligence*")
        st.divider()

        if is_logged_in():
            st.markdown(f"👤 **{st.session_state.username}**")
            st.markdown(f"🔖 Role: `{st.session_state.user_role}`")
            st.divider()
            pages = [
                "🔬 Trial Matching",
                "👤 Patient Profile",
                "💬 Chat with Trials",
                "📋 Browse Trials",
            ]
            if st.session_state.user_role == "admin":
                pages.append("⚙️ Admin")
            selection = st.radio("Navigate", pages, label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout"):
                logout()
        else:
            selection = "🔐 Login / Register"
            st.info("Please log in to access ClinicalMind.")

    return selection


# ══════════════════════════════════════════════════════════
# PAGE 1 — LOGIN / REGISTER
# ══════════════════════════════════════════════════════════
def page_auth():
    st.markdown('<div class="main-header">🧬 ClinicalMind</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">AI Clinical Trial Intelligence & Patient Matching Engine</div>',
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("### 🔑 Login")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    data={"username": username, "password": password},
                    timeout=20,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    # Fetch user info
                    me_resp = requests.get(
                        f"{BACKEND_URL}/auth/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                        timeout=10,
                    )
                    if me_resp.status_code == 200:
                        me = me_resp.json()
                        st.session_state.username = me["username"]
                        st.session_state.user_role = me["role"]
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {resp.json().get('detail', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")

    with col_r:
        st.markdown("### 📝 Register")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            new_email = st.text_input("Email", key="reg_email", placeholder="your@email.com")
            new_password = st.text_input("Password", type="password", key="reg_pass", placeholder="Min 6 characters")
            role = st.selectbox("Role", ["patient", "doctor", "admin"])
            reg_submitted = st.form_submit_button("Register", use_container_width=True)

        if reg_submitted:
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "username": new_username,
                        "email": new_email,
                        "password": new_password,
                        "role": role,
                    },
                    timeout=20,
                )
                if resp.status_code == 201:
                    st.success("✅ Registration successful! Please login.")
                else:
                    st.error(f"Registration failed: {resp.json().get('detail', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")


# ══════════════════════════════════════════════════════════
# PAGE 2 — PATIENT PROFILE
# ══════════════════════════════════════════════════════════
def page_profile():
    st.markdown("## 👤 Patient Profile")
    st.markdown("Describe your medical condition in plain English. Our AI will extract structured entities.")
    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### Create New Profile")
        with st.form("create_profile_form"):
            description = st.text_area(
                "Medical Description",
                height=200,
                placeholder=(
                    "Example: I am a 45-year-old male with stage 2 non-small cell lung cancer "
                    "(NSCLC) diagnosed 8 months ago. I have completed 4 cycles of carboplatin "
                    "and paclitaxel. I have a KRAS mutation. No brain metastases."
                ),
            )
            create_btn = st.form_submit_button("🔬 Extract Entities & Save", use_container_width=True)

        if create_btn:
            if len(description.strip()) < 10:
                st.warning("Please provide a more detailed description.")
            else:
                with st.spinner("🤖 Extracting medical entities with AI..."):
                    resp = api_post("/profile/", {"raw_description": description})
                if resp and resp.status_code == 201:
                    st.success("✅ Profile created and entities extracted!")
                    data = resp.json()
                    entities = data.get("extracted_entities", {})
                    st.session_state["last_profile"] = data
                    st.json(entities)
                elif resp:
                    st.error(f"Error: {resp.json().get('detail', 'Unknown')}")

    with col_right:
        st.markdown("### My Profiles")
        resp = api_get("/profile/my/all")
        if resp and resp.status_code == 200:
            profiles = resp.json()
            if not profiles:
                st.info("No profiles yet. Create one on the left!")
            for p in profiles:
                with st.expander(f"📋 Profile #{p['id']} — {p['created_at'][:10]}"):
                    st.write("**Raw Description:**")
                    st.write(p["raw_description"])
                    st.write("**Extracted Entities:**")
                    entities = p.get("extracted_entities") or {}
                    if entities:
                        df = pd.DataFrame([
                            {"Field": k, "Value": str(v)}
                            for k, v in entities.items()
                        ])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.write("No entities extracted.")


# ══════════════════════════════════════════════════════════
# PAGE 3 — TRIAL MATCHING
# ══════════════════════════════════════════════════════════
def page_matching():
    st.markdown("## 🔬 Trial Matching")
    st.markdown("Match your patient profile to the most relevant active clinical trials.")
    st.divider()

    # Load profiles
    resp = api_get("/profile/my/all")
    if not resp or resp.status_code != 200:
        st.error("Could not load profiles.")
        return

    profiles = resp.json()
    if not profiles:
        st.warning("No patient profiles found. Please create a profile first!")
        return

    profile_options = {f"Profile #{p['id']} ({p['created_at'][:10]})": p["id"] for p in profiles}
    selected_label = st.selectbox("Select Patient Profile", list(profile_options.keys()))
    selected_id = profile_options[selected_label]
    top_k = st.slider("Number of Matches", min_value=1, max_value=10, value=5)

    if st.button("🎯 Find Matching Trials", use_container_width=True):
        with st.spinner("Searching for matching trials using semantic AI..."):
            resp = api_post("/match/", {"profile_id": selected_id, "top_k": top_k})

        if resp and resp.status_code == 200:
            matches = resp.json()
            if not matches:
                st.info("No matching trials found. The database may need syncing.")
                return

            st.success(f"Found {len(matches)} matching trials!")
            for i, m in enumerate(matches, 1):
                trial = m["trial"]
                score = m["similarity_score"]
                with st.container():
                    st.markdown(
                        f"""<div class="trial-card">
                        <h4>#{i} — {trial['title'] or 'Untitled Trial'}</h4>
                        <span class="badge badge-recruiting">{trial['status']}</span>
                        <span class="badge badge-phase">{trial['phase']}</span>
                        <span class="badge badge-phase">NCT: {trial['nct_id']}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        conditions = trial.get("conditions") or []
                        if conditions:
                            st.write(f"**Conditions:** {', '.join(str(c) for c in conditions[:5])}")
                        if trial.get("summary"):
                            st.write(f"**Summary:** {trial['summary'][:300]}...")
                    with col2:
                        st.metric("Similarity", f"{score:.1%}")
                        st.progress(min(score, 1.0))

                    if st.button(f"📊 Explain My Eligibility for {trial['nct_id']}", key=f"explain_{i}"):
                        with st.spinner("🤖 Agent analyzing your eligibility..."):
                            explain_resp = api_post(
                                "/match/explain",
                                {"profile_id": selected_id, "nct_id": trial["nct_id"]},
                            )
                        if explain_resp and explain_resp.status_code == 200:
                            data = explain_resp.json()
                            with st.expander("🔍 Eligibility Assessment", expanded=True):
                                st.write(data.get("assessment", "No assessment available."))
                        elif explain_resp:
                            st.error(explain_resp.json().get("detail", "Error"))

        elif resp:
            st.error(f"Error: {resp.json().get('detail', 'Unknown error')}")


# ══════════════════════════════════════════════════════════
# PAGE 4 — CHAT WITH TRIALS
# ══════════════════════════════════════════════════════════
def page_chat():
    st.markdown("## 💬 Chat with Clinical Trials")
    st.markdown("Ask any question about clinical trials. Our AI answers based on the trial database.")
    st.divider()

    nct_filter = st.text_input(
        "Filter by NCT ID (optional)",
        placeholder="e.g. NCT04292899 — leave blank to search all trials",
    )

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-message-user">👤 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="chat-message-ai">🧬 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
                if msg.get("sources"):
                    st.caption(f"Sources: {', '.join(msg['sources'])}")

    st.divider()
    with st.form("chat_form", clear_on_submit=True):
        user_question = st.text_area("Your question", placeholder="What are the eligibility criteria for lung cancer trials?", height=80)
        send_btn = st.form_submit_button("Send 📤", use_container_width=True)

    if send_btn and user_question.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.spinner("🔍 Searching trial documents and generating answer..."):
            payload = {"question": user_question}
            if nct_filter.strip():
                payload["nct_id"] = nct_filter.strip()
            resp = api_post("/chat/", payload)

        if resp and resp.status_code == 200:
            data = resp.json()
            answer = data.get("answer", "")
            sources = data.get("source_trial_ids", [])
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        elif resp:
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"Error: {resp.json().get('detail', 'Unknown')}", "sources": []}
            )
        st.rerun()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()


# ══════════════════════════════════════════════════════════
# PAGE 5 — BROWSE TRIALS
# ══════════════════════════════════════════════════════════
def page_browse():
    st.markdown("## 📋 Browse Clinical Trials")
    st.divider()

    # Stats
    stats_resp = api_get("/trials/stats")
    if stats_resp and stats_resp.status_code == 200:
        stats = stats_resp.json()
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total Trials", stats.get("total_trials", 0))
        last_sync = stats.get("last_synced", "Never")
        if last_sync and last_sync != "Never":
            last_sync = last_sync[:19].replace("T", " ")
        col2.metric("🕐 Last Synced", last_sync)
        phase_dist = stats.get("phase_distribution", {})
        col3.metric("🔬 Phases Tracked", len(phase_dist))

        if phase_dist:
            with st.expander("📊 Phase Distribution"):
                df_phase = pd.DataFrame(
                    [{"Phase": k, "Count": v} for k, v in phase_dist.items()]
                ).sort_values("Count", ascending=False)
                st.bar_chart(df_phase.set_index("Phase"))

    st.divider()

    # Filter and pagination
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        search_condition = st.text_input("Search by Condition", placeholder="e.g. lung cancer, diabetes...")
    with col_b:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col_c:
        page_size = st.selectbox("Per Page", [10, 20, 50], index=1)

    skip = (page_num - 1) * page_size
    params = {"skip": skip, "limit": page_size}
    if search_condition.strip():
        params["condition"] = search_condition.strip()

    resp = api_get("/trials/", params=params)
    if not resp or resp.status_code != 200:
        st.error("Could not load trials.")
        return

    trials = resp.json()
    if not trials:
        st.info("No trials found for the current filter.")
        return

    st.write(f"Showing {len(trials)} trials.")

    for trial in trials:
        conditions = trial.get("conditions") or []
        cond_str = ", ".join(str(c) for c in conditions[:4]) if conditions else "N/A"
        with st.expander(f"🧬 {trial['nct_id']} — {trial['title'] or 'Untitled'}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Status:** {trial['status']}")
                st.write(f"**Phase:** {trial['phase']}")
                st.write(f"**Conditions:** {cond_str}")
                if trial.get("summary"):
                    st.write(f"**Summary:** {trial['summary'][:400]}...")
            with col2:
                st.write(f"**NCT ID:** `{trial['nct_id']}`")
                last_synced = (trial.get("last_synced") or "")[:10]
                st.write(f"**Last Synced:** {last_synced}")
                interventions = trial.get("interventions") or []
                if interventions:
                    st.write(f"**Interventions:** {len(interventions)} listed")
            if trial.get("eligibility_criteria"):
                st.write("**Eligibility Criteria (excerpt):**")
                st.code(trial["eligibility_criteria"][:600], language=None)


# ══════════════════════════════════════════════════════════
# PAGE 6 — ADMIN
# ══════════════════════════════════════════════════════════
def page_admin():
    st.markdown("## ⚙️ Admin Panel")
    st.divider()

    st.markdown("### 🔄 Trial Sync")
    st.info("Trigger a manual sync of recruiting trials from ClinicalTrials.gov.")
    if st.button("🚀 Trigger Manual Sync", use_container_width=True):
        resp = api_post("/trials/sync", {})
        if resp and resp.status_code == 200:
            data = resp.json()
            st.success(f"✅ Sync triggered! Task ID: `{data.get('task_id')}`")
        elif resp:
            st.error(f"Error: {resp.json().get('detail', 'Unknown')}")


# ══════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════
def main():
    selection = render_sidebar()

    if not is_logged_in():
        page_auth()
        return

    if selection == "👤 Patient Profile":
        page_profile()
    elif selection == "🔬 Trial Matching":
        page_matching()
    elif selection == "💬 Chat with Trials":
        page_chat()
    elif selection == "📋 Browse Trials":
        page_browse()
    elif selection == "⚙️ Admin":
        page_admin()


if __name__ == "__main__":
    main()
