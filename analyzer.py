import os
import json
from pathlib import Path
from groq import Groq
import PIL.Image
from dotenv import load_dotenv
import time
import base64

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Prompt 1 : Ad-analysis 
AD_PROMPT = """You are analyzing a boAt ad creative. boAt is an Indian consumer brand selling earbuds, headphones, speakers, and smartwatches — targeting young, urban Indians.
 
Ad copy: "{copy}"
Platform: {platform}
 
Study the image carefully. Describe what you literally see BEFORE you score anything. Do not infer what is not visible.
Return ONLY valid JSON — no markdown fences, no extra text, nothing outside the JSON object.

{{
  "image_description": "exactly what is in the image: product, people, colors, text overlays, background",
  "hook": "the single element — visual or text — that first grabs attention",
  "cta": "exact CTA wording and where it appears, or 'None visible'",
  "visual_style": "exactly one of: Product-Only | Lifestyle | UGC | Offer-Discount | Celebrity-Influencer | Graphic-Typography",
  "emotion_targeted": "primary emotion this ad targets — e.g. aspiration, FOMO, pride, trust, humor, urgency",
  "scores": {{
    "hook_strength": {{
      "score": 0,
      "reason": "one sentence explaining why this score"
    }},
    "cta_clarity": {{
      "score": 0,
      "reason": "one sentence explaining why this score"
    }},
    "visual_copy_alignment": {{
      "score": 0,
      "reason": "one sentence explaining why this score"
    }},
    "offer_clarity": {{
      "score": 0,
      "reason": "one sentence explaining why this score"
    }}
  }},
  "total_score": 0,
  "verdict": "one sentence on why this ad will or won't stop the scroll"
}}
 
Scoring guide (each dimension is 0-25):
- hook_strength: does the first thing you see/read make you stop scrolling?
- cta_clarity: is the desired action obvious and frictionless?
- visual_copy_alignment: do the image and text reinforce the same single message?
- offer_clarity: is the value proposition immediately understandable without reading twice?
 
total_score MUST equal the exact sum of all four scores."""


# Prompt 2: Corss-ad patterns
PATTERNS_PROMPT = """You have analyzed {n} boAt ad creatives. Here are the results sorted by score (highest first):
 
{analyses}
 
Do two things:
 
1. Look at the top 3 ads. Identify exactly what they have in common — be specific about visual style, hook type, copy tone, emotion, product focus. Avoid vague words like "engaging" or "good".
 
2. Generate 5 concrete creative ideas for boAt to test next. Each idea must:
   - Reference a specific pattern you observed OR a visible gap in the current creative set
   - Name the ad format
   - Describe the hook in one specific sentence (what does the viewer see in the first 2 seconds?)
   - State the CTA
 
Return ONLY valid JSON — no markdown, no extra text:
 
{{
  "top_performer_patterns": [
    "pattern 1 — be specific",
    "pattern 2 — be specific",
    "pattern 3 — be specific"
  ],
  "test_ideas": [
    {{
      "title": "short memorable name",
      "format": "e.g. Static Instagram Post, Reels/Short-form video, Carousel, Story",
      "hook": "specific description of what stops the scroll",
      "cta": "exact CTA text and mechanic",
      "rationale": "which observed pattern or gap this tests, and why it might outperform current creatives"
    }}
  ]
}}"""


# Core Functions
def _encode_image(image_path : str) ->tuple[str, str] :
    path = Path(image_path)
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), mime
    
def anaylze_ad(ad: dict) ->  dict:
    """
    Analyze a single ad.
    Return a structured dictionary with score.
    """
    #time.sleep(4)
    b64, mime = _encode_image(ad["image_path"])
    prompt = AD_PROMPT.format(copy=ad["copy"], platform=ad.get("platform", "unknown"))

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    text = response.choices[0].message.content.strip()

    # Strip markdown fences if the model ignores instructions
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])  # drop first and last line
 
    result = json.loads(text)

    # Source fields
    result["id"] = ad["id"]
    result["image_path"] = ad["image_path"]
    result["copy"] = ad["copy"]
    result["platform"] = ad.get("platform", "unknown")

    # Recompute score 
    s = result["scores"]
    result["total_score"] = (
        s["hook_strength"]["score"]
        + s["cta_clarity"]["score"]
        + s["visual_copy_alignment"]["score"]
        + s["offer_clarity"]["score"]
    )

    return result

def get_patterns_ideas(analyses : list[dict]) -> dict:
    """
    Single LLM call over all results.
    Returns pattern analysis and test ideas.
    """

    sorted_ads = sorted(analyses,key= lambda x: x["total_score"], reverse=True)

    summary = [
        {
            "id": a["id"],
            "total_score": a["total_score"],
            "visual_style": a["visual_style"],
            "hook": a["hook"],
            "emotion_targeted": a["emotion_targeted"],
            "verdict": a["verdict"],
            "cta": a["cta"],
            "scores": {k: v["score"] for k, v in a["scores"].items()},
        }
        for a in sorted_ads
    ]

    prompt = PATTERNS_PROMPT.format(n = len(summary), analyses = json.dumps(summary, indent=2))

    for attempt in range(3):  # retry up to 3 times
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            time.sleep(2)
            continue

    return {"top_performer_patterns": [], "test_ideas": []}