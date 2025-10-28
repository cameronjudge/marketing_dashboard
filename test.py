import streamlit as st, plotly.io as pio, plotly.express as px, pandas as pd

st.set_page_config(page_title="Judge.me Insights", page_icon="✅", layout="wide")



st.markdown("""
<style>
:root{
  --jm-keppel:#3EB2A2;
  --jm-indigo:#0E415F;
  --jm-tea:#C8F9D5;
  --jm-honey:#E9FFEF;
  --jm-peri:#B8BFF1;
  --jm-picton:#57AEE0;
}

html, body, [class*="css"] {
  font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  color: var(--jm-indigo);
}

/* Headings in Gelica (or fallbacks) */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: "Gelica", "Fraunces", "Playfair Display", Georgia, serif;
  letter-spacing: -0.2px;
}

/* Section/card */
.jm-card{
  background: var(--jm-honey);
  border: 1px solid rgba(14,65,95,0.08);
  border-radius: 20px;
  padding: 20px 22px;
}

/* Badge */
.jm-badge{
  display:inline-flex; align-items:center; gap:.4rem;
  background: var(--jm-tea); color: var(--jm-indigo);
  padding: 2px 10px; border-radius:999px; font-weight:600; font-size: .85rem;
}

/* Primary button */
.stButton>button{
  background: var(--jm-keppel); color:#fff; border:none;
  border-radius: 12px; padding:.6rem 1rem; font-weight:700;
}
.stButton>button:hover{ filter:brightness(.96); }

/* Reduce chart-container padding slightly on wide layout */
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)



import plotly.io as pio

pio.templates["judge_me"] = dict(
  layout=dict(
    font=dict(family="Inter, system-ui, sans-serif", size=14, color="#0E415F"),
    title=dict(font=dict(family="Gelica, Fraunces, Georgia, serif", size=28, color="#0E415F")),
    colorway=["#0E415F", "#3EB2A2", "#57AEE0", "#B8BFF1", "#A2EEB7", "#C8F9D5"],
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    margin=dict(l=56, r=36, t=64, b=56),
    xaxis=dict(gridcolor="rgba(14,65,95,0.10)", zeroline=False, linecolor="rgba(14,65,95,0.25)",
               ticks="outside", tickcolor="rgba(14,65,95,0.25)"),
    yaxis=dict(gridcolor="rgba(14,65,95,0.10)", zeroline=False, linecolor="rgba(14,65,95,0.25)",
               ticks="outside", tickcolor="rgba(14,65,95,0.25)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                bgcolor="rgba(255,255,255,0.70)"),
    hoverlabel=dict(font=dict(family="Inter, system-ui, sans-serif", size=13),
                    bgcolor="#E9FFEF", bordercolor="#3EB2A2")
  )
)
pio.templates.default = "judge_me"


df = pd.DataFrame({"Month":["Jan","Feb","Mar","Apr","May","Jun"],"Reviews":[120,160,180,210,260,300]})

left, right = st.columns([2,1], gap="large")
with left:
    fig = px.area(df, x="Month", y="Reviews", title="Monthly Reviews")
    fig.update_traces(line_color="#0E415F", line_width=3.2, fillcolor="rgba(200,249,213,0.26)")
    # last-point emphasis in Keppel
    last_x, last_y = df["Month"].iloc[-1], df["Reviews"].iloc[-1]
    fig.add_scatter(x=[last_x], y=[last_y], mode="markers", marker=dict(size=10, color="#3EB2A2"), showlegend=False)
    # optional goal line
    # fig.add_hline(y=250, line_color="#3EB2A2", line_dash="dot")
    st.plotly_chart(fig, use_container_width=True, theme=None)

with right:
    st.markdown(
        """
        <div class="jm-card">
          <span class="jm-badge">✅ Verified</span>
          <h2 style="margin:.4rem 0 0 0;">Store Health</h2>
          <p style="margin:.25rem 0 1rem 0;">All systems go.</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.button("Export CSV")

