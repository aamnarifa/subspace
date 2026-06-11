import re

def score_contact(contact):
    """
    Computes a lead score based on the contact's job title.
    Matches aliases and handles word boundaries to prevent substring match bugs.
    Rules: CEO=50, Founder=45, CTO=40, VP=30, Director=20.
    """
    score = 0
    title = contact.get("title", "").strip().lower()

    if re.search(r'\b(ceo|chief executive officer)\b', title):
        score += 50
    elif re.search(r'\b(founder|co-founder|cofounder)\b', title):
        score += 45
    elif re.search(r'\b(cto|chief technology officer)\b', title):
        score += 40
    elif re.search(r'\b(vp|vice president|vice-president)\b', title):
        score += 30
    elif re.search(r'\b(director)\b', title):
        score += 20

    return score