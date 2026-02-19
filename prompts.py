def campaign_prompt(data: dict) -> str:
    return f"""
Create a marketing campaign with structured sections.

Brand: {data.get("brand")}
Product/Service: {data.get("product")}
Target Audience: {data.get("audience")}
Platform: {data.get("platform")}
Goal: {data.get("goal")}
Tone: {data.get("tone")}
Length: {data.get("length")}

Return output in these headings:
1) Campaign Idea
2) Value Proposition
3) 3 Ad Copies
4) Hashtags
5) CTA
6) Posting Schedule (3 days)
"""

def pitch_prompt(data: dict) -> str:
    return f"""
Generate a personalized sales pitch.

Company: {data.get("company")}
Customer Persona: {data.get("persona")}
Pain Point: {data.get("pain")}
Product: {data.get("product")}
Tone: {data.get("tone")}
Length: {data.get("length")}

Return:
1) 30-sec Pitch
2) Email Pitch
3) LinkedIn DM Pitch
4) Objection Handling (3 objections)
"""

def lead_prompt(data: dict) -> str:
    return f"""
Score this lead from 0-100 and explain.

Lead Name: {data.get("name")}
Budget: {data.get("budget")}
Need: {data.get("need")}
Urgency: {data.get("urgency")}
Authority: {data.get("authority")}
Industry: {data.get("industry")}

Return:
- Score (0-100)
- Probability of conversion (%)
- Hot/Warm/Cold label
- Reasons (bullet points)
- Next best actions (3)
"""
