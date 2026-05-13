import os
import json
from pathlib import Path
import streamlit as st
from analyzer import anaylze_ad, get_patterns_ideas

# Page config
st.set_page_config(
    page_title= "Ads Analyzer",
    layout="wide"
)

RESULT_FILE = "results.json"
IDEAS_FILE = "ideas.json"

# Load add.json
@st.cache_data
def load_ads() :
    with open("ads.json", encoding="utf-8") as f :
        return json.load(f)
    
ads = load_ads()

# Session state
if "results" not in st.session_state :
    st.session_state.results = []
if "ideas" not in st.session_state :
    st.session_state.ideas = {}

if not st.session_state.results and Path(RESULT_FILE).exists():
    try:
        with open(RESULT_FILE, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                st.session_state.results = json.loads(content)
    except Exception:
        Path(RESULT_FILE).unlink(missing_ok=True)  # delete the broken file

if not st.session_state.ideas and Path(IDEAS_FILE).exists():
    try:
        with open(IDEAS_FILE, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                st.session_state.ideas = json.loads(content)
    except Exception:
        Path(IDEAS_FILE).unlink(missing_ok=True)


# Sidebar
with st.sidebar :
    st.title("Ad Analyzer")
    st.caption(f"{len(ads)} creative(s) loaded.")
    st.divider()

    run_btn = st.button("Run Full Analysis", type="primary", use_container_width=True)

    if Path(RESULT_FILE).exists():
        st.caption("Cached results available")
        if st.button("Clear cache and rerun", use_container_width=True):
            Path(RESULT_FILE).unlink(missing_ok=True)
            Path(IDEAS_FILE).unlink(missing_ok=True)
            st.session_state.results = []
            st.session_state.ideas = {}
            st.rerun()

    st.divider()
    st.markdown("**Scoring Dimensions**")
    st.markdown("""
                - Hook Strength /25
- CTA Clarity /25  
- Visual-Copy Alignment /25
- Offer Clarity /25""")
    

# Run analysis
if run_btn :
    results = []
    bar = st.progress(0, text="Starting analysis...")

    for i, ad in enumerate(ads):
        bar.progress(i /len(ads), text=f"Analyzing ad {ad['id']} of {len(ads)}...")

        try :
            result = anaylze_ad(ad)
            results.append(result)

        except Exception as e :
            st.warning(f"Ad {ad['id']} failed: {e}")

    
    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    bar.progress(0.95, text="Generating Patterns and Ideas...")
    
    try :
        ideas = get_patterns_ideas(results)
        with open(IDEAS_FILE, "w") as f:
            json.dump(ideas, f, indent=2)
        st.session_state.ideas = ideas

    except Exception as e:
        st.warning(f"Pattern genration failed: {e}")
        ideas = {}

    bar.progress(1.0, text="Done!")
    st.session_state.results = results
    bar.empty()
    st.success(f"Analyzed {len(results)} ads successfully.")


# Main content
if not st.session_state.results :
    st.title("Ads Analyzer")
    st.info("Click **Run Full Analysis** in the sidebar to start")
    st.stop()

results = st.session_state.results
ideas = st.session_state.ideas
sorted_results = sorted(results, key=lambda x: x["total_score"], reverse=True)

tab1, tab2, tab3 = st.tabs(["Per-ad Breakdown", "Rankings and Patterns", "What to do Next"])

# Tab 1: Per Ad Breakdown
with tab1:
    st.subheader("Structred Breakdown")
    for r in results :
        score_color = "🟢" if r["total_score"] >= 70 else "🟡" if r["total_score"] >= 50 else "🔴"
        with st.expander(
            f"{score_color} Ad {r['id']}  ·  {r['visual_style']}  ·  {r['platform']}  ·  **{r['total_score']}/100**",
            expanded=False
        ):
            col_img, col_info = st.columns([1,2])

            with col_img :
                st.image(r["image_path"], use_container_width=True)

            with col_info:
                st.markdown(f"**Copy:** {r['copy']}")
                st.markdown(f"**Hook:** {r['hook']}")
                st.markdown(f"**CTA:** {r['cta']}")
                st.markdown(f"**Emotion targeted:** {r['emotion_targeted']}")
                st.markdown(f"**Image:** {r['image_description']}")
 
                st.divider()

                dim_labels = {
                    "hook_strength": "Hook Strength",
                    "cta_clarity": "CTA Clarity",
                    "visual_copy_alignment": "Visual-Copy Alignment",
                    "offer_clarity": "Offer Clarity",
                }
                for key, label in dim_labels.items():
                    s = r["scores"][key]
                    st.markdown(f"**{label}:** {s['score']}/25 ~ {s['reason']}")

                st.divider()
                st.markdown(f"**Verdict:** _{r['verdict']}_")
                st.metric("Total Score", f"{r['total_score']} / 100")

# Tab 2
with tab2:
    st.subheader("Performance Ranking")

    for rank, r in enumerate(sorted_results, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
        col_img, col_detail = st.columns([1, 4])

        with col_img:
            st.image(r["image_path"], use_container_width=True)

        with col_detail:
            st.markdown(f"**{medal} Ad {r['id']}** · {r['visual_style']} · {r['platform']}")
            st.progress(r["total_score"] / 100, text=f"{r['total_score']}/100")
            st.caption(r["verdict"])

        st.divider()


    if ideas.get("top_performer_patterns") :
        st.subheader("What the Top Ads Have in Common")
        for p in ideas["top_performer_patterns"]:
            st.markdown(f"- {p}")

# Tab 3
with tab3:
    if ideas.get("test_ideas") :
        st.subheader("5 Creative ideas to test next")
        

        for i, idea in enumerate(ideas['test_ideas'], 1):
            with st.container(border=True):
                st.markdown(f"### {i}. {idea['title']}")
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown(f"**Format:** {idea['format']}")
                    st.markdown(f"**Hook:** {idea['hook']}")
                with col_b:
                    st.markdown(f"**CTA:** {idea['cta']}")
                    st.markdown(f"**Why this:** {idea['rationale']}")

    else :
        st.info("Run analysis to generate test ideas.")