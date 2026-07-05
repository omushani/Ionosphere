

import streamlit as st


def inject_base_style() -> None:
    st.markdown(
        """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;1,9..40,400&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 800px at 10% -10%, rgba(0, 212, 255, 0.08), transparent 55%),
                radial-gradient(900px 600px at 100% 0%, rgba(0, 140, 255, 0.06), transparent 50%),
                #050508 !important;
  }

  .block-container {
    padding-top: 1.25rem !important;
    max-width: 1200px;
  }

  h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 0.04em;
    color: #e8f7ff !important;
    text-shadow: 0 0 18px rgba(0, 212, 255, 0.45);
  }

  p, span, label {
    font-family: 'DM Sans', system-ui, sans-serif !important;
    color: #dbefff !important;
  }

  [data-testid="stTextInput"] input {
    background: #0c1018 !important;
    color: #e8f7ff !important;
    border: 1px solid rgba(0, 212, 255, 0.35) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.12) inset;
  }

  [data-testid="stButton"] button {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.25), rgba(0, 120, 255, 0.2)) !important;
    color: #e8f7ff !important;
    border: 1px solid rgba(0, 212, 255, 0.55) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.25);
  }

  [data-testid="stButton"] button:hover {
    border-color: #00d4ff !important;
    box-shadow: 0 0 28px rgba(0, 212, 255, 0.45);
  }

  div[data-testid="stExpander"] {
    background: rgba(12, 16, 24, 0.85);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
  }

  div[data-testid="stExpander"] details summary p {
    color: #e8f7ff !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em;
  }

  .neon-card {
    background: linear-gradient(145deg, rgba(12, 16, 24, 0.92), rgba(8, 12, 20, 0.92));
    border: 1px solid rgba(0, 212, 255, 0.28);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.05), 0 12px 40px rgba(0, 0, 0, 0.45),
                0 0 24px rgba(0, 212, 255, 0.12);
    margin-bottom: 0.5rem;
  }

  .neon-pill {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    border: 1px solid rgba(0, 212, 255, 0.45);
    color: #00d4ff !important;
    box-shadow: 0 0 16px rgba(0, 212, 255, 0.2);
  }

  .top-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.35rem 0 1.1rem 0;
    border-bottom: 1px solid rgba(0, 212, 255, 0.18);
    margin-bottom: 1rem;
  }

  .top-nav-wrap {
    border: 1px solid rgba(0, 212, 255, 0.22);
    border-radius: 14px;
    padding: 0.25rem 0.75rem 0.45rem 0.75rem;
    margin-bottom: 0.8rem;
    background: linear-gradient(145deg, rgba(12, 16, 24, 0.9), rgba(8, 12, 20, 0.9));
    box-shadow: 0 0 26px rgba(0, 212, 255, 0.12);
  }

  .brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #e8f7ff;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
    letter-spacing: 0.12em;
  }

  .nav-links a {
    color: #9bdfff !important;
    text-decoration: none !important;
    margin-left: 1rem;
    font-weight: 600;
  }

  .nav-links a:hover {
    color: #00d4ff !important;
    text-shadow: 0 0 14px rgba(0, 212, 255, 0.6);
  }
</style>
""",
        unsafe_allow_html=True,
    )


def render_top_bar() -> None:
    """Site name + Home/About using Streamlit navigation (no sidebar menus)."""
    st.markdown('<div class="top-nav-wrap">', unsafe_allow_html=True)
    left, mid, right = st.columns([3.2, 1.1, 1.1])
    with left:
        st.markdown(
            '<p class="brand" style="margin:0;padding:0.35rem 0 0 0;">IONOSPHERE</p>',
            unsafe_allow_html=True,
        )
    with mid:
        st.page_link("app.py", label="Home", use_container_width=True)
    with right:
        st.page_link("pages/About.py", label="About", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
