from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.config import EVALUATION_DIR, get_settings
from app.data.loader import events_for_tail, known_tails, load_events, load_faa_sample
from backend.agent.llm import DiagnosisAgent, GroqAPIError, GroqConfigurationError
from backend.memory.hindsight_client import (
    HindsightAPIError,
    HindsightClient,
    HindsightConfigurationError,
)
st.set_page_config(
    page_title="TailMemory",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root{
  --bg:#111447;
  --bg2:#151950;
  --panel:#1a1d58;
  --panel2:#202461;
  --line:#3d417b;
  --text:#f5f6ff;
  --muted:#aeb4d5;

  --pink:#f36b9b;
  --cyan:#50d9e8;
  --purple:#8c82e8;
  --mint:#83e2b0;
  --yellow:#f4d56d;
  --red:#f46f86;
  --white:#ffffff;

  --sans:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:'Space Mono',ui-monospace,Consolas,monospace;
}

.stApp{
  background:
    radial-gradient(circle at 12% 8%,rgba(243,107,155,.13),transparent 24%),
    radial-gradient(circle at 88% 12%,rgba(80,217,232,.12),transparent 24%),
    linear-gradient(135deg,#111447 0%,#151950 52%,#101342 100%);
  color:var(--text);
  font-family:var(--sans);
}

#MainMenu,
footer{
  visibility:hidden;
}

[data-testid="stHeader"]{
  background:rgba(17,20,71,.78);
  backdrop-filter:blur(10px);
}

.block-container{
  padding:2rem 2.4rem 3rem;
  max-width:1400px;
}

/* SIDEBAR */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#171a52,#111447);
  border-right:1px solid #34386e;
}

[data-testid="stSidebar"] *{
  color:var(--text);
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label{
  color:var(--muted)!important;
}

/* HEADINGS */
h1,
h2,
h3{
  font-family:var(--sans)!important;
  color:var(--text)!important;
  letter-spacing:.01em;
}

h1{
  font-weight:700;
}

h2{
  font-size:1.02rem!important;
  font-weight:700;
  text-transform:uppercase;
  letter-spacing:.08em;
  border:0!important;
  padding:0 0 .7rem!important;
  margin-top:1.8rem!important;
  position:relative;
}

h2:after{
  content:"";
  display:block;
  width:62px;
  height:3px;
  margin-top:8px;
  border-radius:5px;
  background:linear-gradient(
    90deg,
    var(--pink),
    var(--purple),
    var(--cyan)
  );
}

/* BUTTONS */
.stButton>button{
  background:#222660;
  border:1px solid #4b4f88;
  color:var(--text);
  font-family:var(--sans);
  font-weight:600;
  letter-spacing:.03em;
  border-radius:8px;
  min-height:42px;
  transition:.18s ease;
}

.stButton>button:hover{
  border-color:var(--cyan);
  color:var(--white);
  background:#292d6b;
  box-shadow:0 0 18px rgba(80,217,232,.16);
  transform:translateY(-1px);
}

.stButton>button[kind="primary"]{
  background:linear-gradient(
    90deg,
    var(--pink),
    #c96bd1
  );
  color:#fff;
  border:none;
  box-shadow:0 8px 24px rgba(243,107,155,.18);
}

.stButton>button[kind="primary"]:hover{
  background:linear-gradient(
    90deg,
    #f579a5,
    #b879e0
  );
  color:#fff;
}

/* INPUTS */
textarea,
input{
  background:#15194d!important;
  color:var(--text)!important;
  border:1px solid #454a82!important;
  font-family:var(--sans)!important;
  border-radius:8px!important;
}

textarea:focus,
input:focus{
  border-color:var(--cyan)!important;
  box-shadow:0 0 0 1px rgba(80,217,232,.65)!important;
}

[data-baseweb="select"]>div{
  background:#181c53;
  border-color:#454a82;
  border-radius:8px;
}

/* EXPANDERS */
[data-testid="stExpander"]{
  background:rgba(27,30,87,.82);
  border:1px solid #3c4178;
  border-radius:10px;
}

[data-testid="stExpander"]:hover{
  border-color:#565c99;
}

/* ALERTS */
.stAlert{
  border-radius:9px!important;
  background:#20235f!important;
  border:1px solid #474c87!important;
}

/* TAILMEMORY HEADER */
.tm-title{
  font-family:var(--sans);
  font-weight:700;
  font-size:2.8rem;
  letter-spacing:.08em;
  color:var(--white);
  margin:0;
  line-height:1.05;
}

.tm-title:after{
  content:"";
  display:block;
  width:92px;
  height:4px;
  margin-top:12px;
  border-radius:8px;
  background:linear-gradient(
    90deg,
    var(--pink),
    var(--purple),
    var(--cyan)
  );
}

.tm-tag{
  color:var(--muted);
  font-size:.95rem;
  line-height:1.55;
  max-width:780px;
  margin:.7rem 0 1rem;
}

/* STATUS PILLS */
.pill{
  display:inline-block;
  font-family:var(--sans);
  font-size:.68rem;
  font-weight:700;
  letter-spacing:.08em;
  padding:5px 11px;
  margin-right:8px;
  border:1px solid var(--c);
  color:var(--c);
  border-radius:999px;
  background:rgba(255,255,255,.035);
}

/* MAIN PANELS */
.panel{
  background:linear-gradient(
    145deg,
    rgba(31,35,96,.96),
    rgba(24,27,77,.96)
  );
  border:1px solid #3e437b;
  border-radius:12px;
  padding:18px 20px;
  position:relative;
  margin-bottom:14px;
  box-shadow:0 10px 30px rgba(4,5,30,.12);
}

.panel::before{
  content:"";
  position:absolute;
  left:0;
  top:12px;
  bottom:12px;
  width:3px;
  border-radius:4px;
  background:var(--a,var(--cyan));
}

/* LABELS */
.label{
  font-family:var(--sans);
  font-size:.67rem;
  font-weight:700;
  letter-spacing:.12em;
  color:var(--muted);
  text-transform:uppercase;
  margin-bottom:8px;
}

/* AIRFRAME READOUT */
.readout{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:12px;
}

.readout>div{
  padding:13px 14px;
  background:rgba(255,255,255,.025);
  border:1px solid #34396f;
  border-radius:9px;
}

.readout .v{
  font-family:var(--mono);
  font-size:1.35rem;
  color:var(--cyan);
}

.readout .bad{
  color:var(--pink);
}

/* BANNERS */
.banner{
  border:1px solid #635a8d;
  background:linear-gradient(
    90deg,
    rgba(243,107,155,.08),
    rgba(140,130,232,.08)
  );
  color:#e9eaff;
  border-radius:9px;
  padding:12px 16px;
  margin-bottom:14px;
}

/* CHIPS */
.chip{
  display:inline-block;
  font-family:var(--sans);
  font-size:.65rem;
  font-weight:700;
  letter-spacing:.08em;
  padding:3px 9px;
  border:1px solid var(--c);
  color:var(--c);
  border-radius:999px;
  background:rgba(255,255,255,.025);
  white-space:nowrap;
}

/* TAGS */
.tag{
  display:inline-block;
  font-family:var(--sans);
  font-size:.76rem;
  padding:5px 10px;
  margin:0 6px 6px 0;
  border:1px solid #464b84;
  border-radius:7px;
  color:var(--text);
  background:#20245f;
}

/* LIST ITEMS */
.item{
  display:flex;
  gap:10px;
  align-items:flex-start;
  justify-content:space-between;
  padding:10px 0;
  border-bottom:1px dashed #414578;
}

.item:last-child{
  border-bottom:none;
}

.eid{
  font-family:var(--mono);
  color:var(--cyan);
  font-size:.74rem;
}

.sub{
  color:var(--muted);
  font-size:.84rem;
}

/* CONFIDENCE METER */
.meter span{
  display:inline-block;
  width:40px;
  height:7px;
  margin-right:5px;
  border-radius:3px;
  background:#3b4075;
}

.meter span.on{
  background:linear-gradient(
    90deg,
    var(--pink),
    var(--purple)
  );
  box-shadow:0 0 10px rgba(243,107,155,.28);
}

/* TIMELINE */
.tl{
  max-height:560px;
  overflow-y:auto;
  padding:4px 8px 0;
}

.tl-item{
  position:relative;
  margin-left:8px;
  padding:0 0 18px 24px;
  border-left:2px solid #3d4177;
}

.tl-item::before{
  content:"";
  position:absolute;
  left:-7px;
  top:3px;
  width:12px;
  height:12px;
  border-radius:50%;
  background:var(--c);
  box-shadow:0 0 12px var(--c);
}

.tl-top{
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
  margin-bottom:3px;
}

/* STREAMLIT METRICS */
[data-testid="stMetric"]{
  background:#1e225d;
  border:1px solid #3e437b;
  border-radius:10px;
  padding:12px;
}

/* DATAFRAMES */
[data-testid="stDataFrame"]{
  border:1px solid #3e437b;
  border-radius:10px;
  overflow:hidden;
}

/* CAPTIONS */
[data-testid="stCaptionContainer"]{
  color:var(--muted);
}

hr{
  border-color:#373c73!important;
}

/* RESPONSIVE */
@media (max-width:900px){
  .block-container{
    padding:1.2rem 1rem 2rem;
  }

  .readout{
    grid-template-columns:repeat(2,1fr);
  }

  .tm-title{
    font-size:2.1rem;
  }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
@st.cache_data
def get_events():
    return load_events()


def _status_label(configured: bool) -> str:
    return "Configured" if configured else "Not configured"


def _render_memory(memory):
    with st.container(border=True):
        event_id = memory.event_id or "Recalled memory"
        status = (memory.outcome_status or "unknown").upper()
        st.markdown(f"**{event_id}** · {status}")
        st.caption(
            f"{memory.date or 'Date not returned'} · ATA {memory.ata_chapter or '—'} · "
            f"{memory.tail_number or 'Tail not returned'}"
        )
        st.write(memory.symptom)
        if memory.action_taken:
            st.write(f"Action: {memory.action_taken}")
        if memory.outcome:
            st.write(f"Outcome: {memory.outcome}")
        st.caption("Source: Hindsight Cloud recall")


def _render_timeline(events):
    if not events:
        st.info("No synthetic maintenance history is available for this tail.")
        return
    frame = pd.DataFrame(
        [
            {
                "Date": event.date,
                "Event": event.event_id,
                "ATA": event.ata_chapter,
                "Symptom": event.symptom,
                "Action": event.action_taken,
                "Status": event.outcome_status.upper(),
                "Source": event.source_type,
            }
            for event in events
        ]
    )
    st.dataframe(frame, use_container_width=True, hide_index=True)


def _render_advisory(result):
    st.subheader("AI Maintenance Advisory")
    st.warning(result.safety_note)
    st.markdown(f"**Fault summary**  \n{result.fault_summary}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Likely fault categories**")
        for item in result.likely_fault_categories:
            st.write(f"- {item}")
    with c2:
        st.markdown("**Previous successful actions**")
        if result.relevant_previous_actions:
            for item in result.relevant_previous_actions:
                st.write(f"- {item}")
        else:
            st.caption("None supported by recalled evidence.")
    with c3:
        st.markdown("**Previous failed actions**")
        if result.failed_actions_to_avoid:
            for item in result.failed_actions_to_avoid:
                st.write(f"- {item}")
        else:
            st.caption("None supported by recalled evidence.")
    st.markdown("**Recommended next verification**")
    for item in result.recommended_next_steps:
        st.write(f"- {item}")
    st.caption(
        f"Confidence: {result.confidence.upper()} · Evidence event IDs: "
        + (", ".join(result.evidence_event_ids) or "none")
    )


def main():
    settings = get_settings()
    events = get_events()
    tails = known_tails(events)

    st.title("TailMemory")
    st.subheader("Maintenance memory for every airframe.")
    st.write(
        "TailMemory is an AI-powered aircraft maintenance assistant that uses historical maintenance records to retrieve similar faults, provide evidence-based insights, and support technicians in diagnosing recurring aircraft issues."
        "A maintenance assistant that remembers what every previous shift already "
        "tried on this airframe."
    )
    st.markdown(
    '<div style="color: white;">'
    'Advisory prototype. Maintenance decisions remain with appropriately qualified '
    'personnel. All aircraft records shown here are synthetic.'
    '</div>',
    unsafe_allow_html=True
)

    with st.sidebar:
        st.header("Aircraft")
        tail_number = st.selectbox("Tail number", tails, index=tails.index("VT-ABC"))
        ata_options = sorted(
            {event.ata_chapter for event in events_for_tail(events, tail_number)}
        )
        ata_filter = st.selectbox("ATA chapter", ["All"] + ata_options)
        st.divider()
        st.caption("Service status")
        st.write(f"Hindsight Cloud: {_status_label(settings.hindsight_configured)}")
        st.write(f"Groq LLM: {_status_label(settings.groq_configured)}")
        if not settings.fully_configured:
            st.warning(
                "Add GROQ_API_KEY, HINDSIGHT_API_KEY, and HINDSIGHT_BANK_ID to run "
                "a live diagnosis. No local memory fallback is used."
            )

    st.header("New Maintenance Fault")
    st.markdown("""
<style>
textarea {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)
    fault = st.text_area(
        
        "Describe the current fault",
        value="Hydraulic pressure warning after takeoff."
        if tail_number == "VT-ABC"
        else "",
        height=110,
        placeholder="Describe the current fault...",
    )
    if st.button("Diagnose with Aircraft Memory", type="primary", use_container_width=True):
        if not fault.strip():
            st.error("Describe the current fault before running a diagnosis.")
        else:
            with st.spinner("Recalling aircraft-specific memory and preparing advisory..."):
                try:
                    memories = HindsightClient(settings).recall_maintenance_events(
                        tail_number, fault.strip()
                    )
                    result = DiagnosisAgent(settings).diagnose(
                        tail_number, fault.strip(), memories
                    )
                    st.session_state["diagnosis"] = result
                    st.session_state["memories"] = memories
                    st.session_state["fault"] = fault.strip()
                    st.session_state["tail_number"] = tail_number
                    st.session_state["feedback_saved"] = False
                except (
                    HindsightConfigurationError,
                    HindsightAPIError,
                    GroqConfigurationError,
                    GroqAPIError,
                ) as error:
                    st.error(str(error))

    diagnosis = st.session_state.get("diagnosis")
    memories = st.session_state.get("memories", [])
    if diagnosis:
        _render_advisory(diagnosis)
        st.subheader("Aircraft-Specific Evidence")
        if memories:
            st.success(
                f"{len(memories)} memory item(s) recalled from Hindsight Cloud for {tail_number}."
            )
            for memory in memories:
                _render_memory(memory)
        else:
            st.info(
                "Hindsight returned no aircraft-specific evidence. General reasoning "
                "must not be presented as aircraft history."
            )
        st.subheader("General Reasoning")
        st.caption(
            "The LLM may infer categories from the current fault, but only recalled "
            "Hindsight items support aircraft-specific claims."
        )

        st.subheader("Record Outcome")
        st.write("What happened after the recommended action?")
        feedback_cols = st.columns(3)
        for column, outcome in zip(
            feedback_cols, ("WORKED", "DID NOT WORK", "NOT YET VERIFIED")
        ):
            if column.button(outcome, key=f"feedback-{outcome}", use_container_width=True):
                try:
                    HindsightClient(settings).retain_feedback(
                        tail_number,
                        st.session_state["fault"],
                        outcome,
                        diagnosis.fault_summary,
                    )
                    st.session_state["feedback_saved"] = True
                except (HindsightConfigurationError, HindsightAPIError) as error:
                    st.error(str(error))
        if st.session_state.get("feedback_saved"):
            st.success("Outcome recorded in aircraft memory.")

    st.header("Hindsight Memory Inspector")
    st.caption(
        "This panel shows exact results returned by the Hindsight Cloud recall operation."
    )
    if diagnosis and memories:
        st.write(f"Memories recalled: {len(memories)}")
        for memory in memories:
            _render_memory(memory)
    else:
        st.info("Run a configured diagnosis to inspect persistent memory results.")

    st.header("Maintenance Timeline")
    timeline_events = events_for_tail(events, tail_number)
    if ata_filter != "All":
        timeline_events = [
            event for event in timeline_events if event.ata_chapter == ata_filter
        ]
    _render_timeline(timeline_events)

    with st.expander("Cross-tail comparison"):
        st.write(
            "Aircraft-specific memory stays scoped to the selected tail. "
            "VT-ABC has a planted hydraulic failed-fix chain; VT-XYZ does not."
        )
        comparison = pd.DataFrame(
            [
                {
                    "Aircraft": tail,
                    "Hydraulic history in synthetic log": "Present"
                    if any(
                        "hydraulic" in event.symptom.lower()
                        for event in events_for_tail(events, tail)
                    )
                    else "Not present",
                    "Record type": "Synthetic",
                }
                for tail in ("VT-ABC", "VT-XYZ")
            ]
        )
        st.dataframe(comparison, use_container_width=True, hide_index=True)

    with st.expander("Evaluation"):
        results_path = EVALUATION_DIR / "results.csv"
        chart_path = EVALUATION_DIR / "results.png"
        if results_path.exists():
            st.dataframe(pd.read_csv(results_path), use_container_width=True, hide_index=True)
            if chart_path.exists():
                st.image(str(chart_path), caption="Measured deterministic evidence proxy")
        else:
            st.info(
                "Run `python -m evaluation.evaluate` from the tailmemory directory "
                "to generate the measured evaluation artifacts."
            )
        st.caption(
            "FAA SDR sample narratives are used only for terminology and context; "
            "they are not records for any synthetic aircraft."
        )
        faa = load_faa_sample()
        if not faa.empty:
            st.dataframe(faa, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
