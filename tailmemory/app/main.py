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
        "A maintenance assistant that remembers what every previous shift already "
        "tried on this airframe."
    )
    st.info(
        "Advisory prototype. Maintenance decisions remain with appropriately qualified "
        "personnel. All aircraft records shown here are synthetic."
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
