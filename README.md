# Ads Creative Analyzer

A lightweight tool that analyzes ad creatives using an LLM — breaking down each ad's structure, scoring likely performance, and surfacing what to test next.


---

## What it does

**Tab 1 — Per-Ad Breakdown**
For each creative, the tool extracts:
- What's in the image (description, visual style, emotion targeted)
- Hook, CTA, and copy
- Scores across 4 dimensions with reasoning

**Tab 2 — Rankings & Patterns**
- All ads ranked by predicted performance score
- What the top 3 ads have in common

**Tab 3 — What to Test Next**
- 5 concrete creative ideas grounded in observed patterns and gaps

---

## Scoring heuristic

Each ad is scored out of 100 across 4 dimensions (25 pts each):

| Dimension | What it measures |
|---|---|
| Hook Strength | Does the first thing you see stop the scroll? |
| CTA Clarity | Is the desired action obvious and frictionless? |
| Visual-Copy Alignment | Do the image and text reinforce the same message? |
| Offer Clarity | Is the value prop immediately understandable? |

The LLM writes a one-line reason for each score before scoring — this forces structured reasoning rather than vibes-based numbers.

---

## Stack

- **Model:** Llama 4 Scout via Groq (free tier)
- **UI:** Streamlit
- **Language:** Python

---

## Project structure

```
ad-analyzer/
├── app.py            # Streamlit UI
├── analyzer.py       # LLM calls, prompts, scoring
├── ads.json          # Ad metadata (id, image_path, copy, platform)
├── ads/              # Ad images
├── requirements.txt
└── .env              # GROQ_API_KEY (not committed)
```

---

## Run locally

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

```bash
streamlit run app.py
```

Results are cached to `results.json` and `ideas.json` after the first run — re-runs won't re-hit the API.

---

## Deploy (Streamlit Cloud)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo
3. Under Settings → Secrets, add:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
4. Deploy

---

## ads.json format

```json
[
  {
    "id": 1,
    "image_path": "ads/1.png",
    "copy": "Ad copy text here",
    "platform": "Instagram"
  }
]
```
