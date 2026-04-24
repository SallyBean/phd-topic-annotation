"""
PhD Topic Annotation App
Multi-label harm taxonomy annotation with Google Sheets backend.
"""
import streamlit as st
import pandas as pd
import uuid
from config import CATEGORIES, RATERS, TYPE_COLOURS
from sheets import load_topics, load_annotations, update_annotation

st.set_page_config(
    page_title="PhD Topic Annotation",
    page_icon="🏷️",
    layout="wide",
)

# ── Session state init ────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "rater" not in st.session_state:
    st.session_state.rater = None
if "topic_idx" not in st.session_state:
    st.session_state.topic_idx = 0
if "selected" not in st.session_state:
    st.session_state.selected = []
if "show_already_coded" not in st.session_state:
    st.session_state.show_already_coded = False

# ── Rater login ───────────────────────────────────────────────────────────────
if st.session_state.rater is None:
    st.title("PhD Topic Annotation")
    st.markdown("### Who are you?")
    rater = st.selectbox("Select your name", ["— select —"] + RATERS)
    if rater != "— select —":
        if st.button("Start annotating →", type="primary"):
            st.session_state.rater = rater
            st.rerun()
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_data():
    topics = load_topics()
    annotations = load_annotations()
    return topics, annotations

topics_df, annotations_df = get_data()

rater = st.session_state.rater

# Topics coded by this rater
rater_ann = annotations_df[annotations_df["rater"] == rater] if len(annotations_df) else pd.DataFrame()
coded_keys = set(
    zip(rater_ann["topic_id"].astype(str), rater_ann["model"].astype(str))
) if len(rater_ann) else set()

# Queue: all topics, uncoded first, then coded (for review)
topics_df["_key"] = list(zip(topics_df["topic_id"].astype(str), topics_df["model"].astype(str)))
uncoded = topics_df[~topics_df["_key"].isin(coded_keys)].reset_index(drop=True)
coded   = topics_df[topics_df["_key"].isin(coded_keys)].reset_index(drop=True)

total   = len(topics_df)
n_coded = len(coded_keys)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**Rater:** {rater}")
    st.markdown(f"**Session:** `{st.session_state.session_id}`")
    st.divider()
    st.progress(n_coded / total if total else 0)
    st.markdown(f"**{n_coded} / {total}** topics coded")
    st.markdown(f"**{total - n_coded}** remaining")
    st.divider()

    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

    show_review = st.toggle("Review my annotations", value=st.session_state.show_already_coded)
    st.session_state.show_already_coded = show_review

    if rater == RATERS[0]:  # admin only
        st.divider()
        st.markdown("**All raters**")
        if len(annotations_df):
            for r in annotations_df["rater"].unique():
                n = len(annotations_df[annotations_df["rater"] == r])
                st.markdown(f"- {r}: {n}/{total}")

    st.divider()
    if st.button("🚪 Switch rater"):
        st.session_state.rater = None
        st.session_state.topic_idx = 0
        st.session_state.selected = []
        st.rerun()

# ── Main area: annotation or review ──────────────────────────────────────────
if total - n_coded == 0 and not show_review:
    st.success(f"🎉 All {total} topics coded! Use the review toggle to check your annotations.")
    st.stop()

queue = coded if show_review else uncoded
if len(queue) == 0:
    st.info("Nothing to show here.")
    st.stop()

# Clamp index
idx = min(st.session_state.topic_idx, len(queue) - 1)
st.session_state.topic_idx = idx
row = queue.iloc[idx]

# Look up existing annotation if reviewing
existing_cats = []
if show_review and len(rater_ann):
    mask = (
        (rater_ann["topic_id"].astype(str) == str(row["topic_id"])) &
        (rater_ann["model"].astype(str) == str(row["model"]))
    )
    hits = rater_ann[mask]
    if len(hits):
        existing_cats = str(hits.iloc[-1]["categories"]).split("|")

# Init selected from existing if entering a new topic
topic_key = f"{row['topic_id']}_{row['model']}"
if st.session_state.get("_last_topic") != topic_key:
    st.session_state.selected = existing_cats if show_review else []
    st.session_state["_last_topic"] = topic_key

# ── Topic display ─────────────────────────────────────────────────────────────
mode_label = "📋 REVIEWING" if show_review else "🏷️ ANNOTATING"
st.markdown(f"### {mode_label} — Topic {idx + 1} of {len(queue)}")

col_nav1, col_info, col_nav2 = st.columns([1, 6, 1])
with col_nav1:
    if st.button("◀ Prev") and idx > 0:
        st.session_state.topic_idx -= 1
        st.rerun()
with col_nav2:
    if st.button("Next ▶") and idx < len(queue) - 1:
        st.session_state.topic_idx += 1
        st.rerun()

st.divider()

col_topic, col_cats = st.columns([2, 3])

with col_topic:
    st.markdown(f"**Model:** `{row['model']}`")
    st.markdown(f"**Topic ID:** `{row['topic_id']}`")
    st.markdown(f"**Documents:** {row.get('document_count', row.get('Document_Count', '?')):,}")
    st.divider()
    keywords = str(row.get("topic_keywords", row.get("Topic_Keywords", "")))
    kw_list = [k.strip() for k in keywords.replace("_", " ").replace(",", " ").split() if k.strip()]
    st.markdown("**Keywords:**")
    st.markdown(" · ".join(f"`{k}`" for k in kw_list[:12]))

with col_cats:
    st.markdown("**Select all applicable categories:**")
    selected = list(st.session_state.selected)

    current_type = None
    for cat_name, cat_type, cat_desc in CATEGORIES:
        if cat_type != current_type:
            current_type = cat_type
            colour = TYPE_COLOURS.get(cat_type, "#555")
            label_map = {
                "explicit": "EXPLICIT HARM",
                "representational": "REPRESENTATIONAL",
                "structural": "STRUCTURAL",
                "crosscutting": "CROSS-CUTTING",
                "none": "NONE / UNCLEAR",
            }
            st.markdown(
                f"<span style='color:{colour};font-size:0.75em;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:1px'>"
                f"{label_map.get(cat_type,'')}</span>",
                unsafe_allow_html=True,
            )

        checked = cat_name in selected
        new_val = st.checkbox(
            f"**{cat_name.replace('_', ' ')}** — {cat_desc}",
            value=checked,
            key=f"cb_{topic_key}_{cat_name}",
        )
        if new_val and cat_name not in selected:
            selected.append(cat_name)
        elif not new_val and cat_name in selected:
            selected.remove(cat_name)

    st.session_state.selected = selected

# ── Save button ───────────────────────────────────────────────────────────────
st.divider()
col_save, col_clear, col_skip = st.columns([2, 1, 1])

with col_save:
    save_label = "💾 Save & Next" if not show_review else "💾 Update annotation"
    if st.button(save_label, type="primary", disabled=len(selected) == 0):
        update_annotation(
            topic_id=int(row["topic_id"]),
            model=str(row["model"]),
            rater=rater,
            categories=selected,
            session_id=st.session_state.session_id,
        )
        st.cache_data.clear()
        st.session_state.selected = []
        if not show_review and idx < len(queue) - 1:
            st.session_state.topic_idx += 1
        st.rerun()

with col_clear:
    if st.button("✕ Clear"):
        st.session_state.selected = []
        st.rerun()

with col_skip:
    if st.button("⏭ Skip (unclear)") and not show_review:
        update_annotation(
            topic_id=int(row["topic_id"]),
            model=str(row["model"]),
            rater=rater,
            categories=["unclear_uncodeable"],
            session_id=st.session_state.session_id,
        )
        st.cache_data.clear()
        st.session_state.selected = []
        if idx < len(queue) - 1:
            st.session_state.topic_idx += 1
        st.rerun()

if selected:
    st.markdown("**Selected:** " + " · ".join(f"`{c}`" for c in selected))
