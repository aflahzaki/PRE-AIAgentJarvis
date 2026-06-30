"""
Writing Tools - Template helpers and text formatting for J.A.R.V.I.S agents.

Provides email, proposal, and social media caption templates, plus text
formatting utilities for academic and casual styles.
All functions return structured dict results with success/error status.

No external dependencies required - pure Python implementation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def email_template(
    tone: str, subject: str, recipient: Optional[str] = None
) -> Dict[str, Any]:
    """Generate an email template based on tone and subject.

    Args:
        tone: Email tone ('formal', 'casual', 'friendly', 'professional').
        subject: Email subject line.
        recipient: Recipient name (optional).

    Returns:
        Dict with 'success' and 'template' string or 'error'.
    """
    if not subject or not subject.strip():
        return {"success": False, "error": "Email subject cannot be empty."}

    valid_tones = ["formal", "casual", "friendly", "professional"]
    if tone not in valid_tones:
        return {
            "success": False,
            "error": "Invalid tone '{}'. Valid: {}".format(
                tone, ", ".join(valid_tones)
            ),
        }

    recipient_name = recipient.strip() if recipient else "[Recipient Name]"

    templates = {
        "formal": (
            "Subject: {subject}\n\n"
            "Dear {recipient},\n\n"
            "I hope this message finds you well. I am writing to you "
            "regarding {subject}.\n\n"
            "[Your message here]\n\n"
            "I would appreciate your prompt attention to this matter. "
            "Please do not hesitate to contact me should you require "
            "any further information.\n\n"
            "Yours sincerely,\n"
            "[Your Name]\n"
            "[Your Title]\n"
            "[Your Contact Information]"
        ),
        "casual": (
            "Subject: {subject}\n\n"
            "Hey {recipient}!\n\n"
            "Hope you're doing great! Just wanted to reach out about "
            "{subject}.\n\n"
            "[Your message here]\n\n"
            "Let me know what you think!\n\n"
            "Cheers,\n"
            "[Your Name]"
        ),
        "friendly": (
            "Subject: {subject}\n\n"
            "Hi {recipient},\n\n"
            "I hope you're having a wonderful day! I wanted to touch base "
            "with you about {subject}.\n\n"
            "[Your message here]\n\n"
            "Looking forward to hearing from you!\n\n"
            "Best wishes,\n"
            "[Your Name]"
        ),
        "professional": (
            "Subject: {subject}\n\n"
            "Dear {recipient},\n\n"
            "I am reaching out regarding {subject}. "
            "I believe this matter requires our attention.\n\n"
            "[Your message here]\n\n"
            "Please let me know your availability to discuss this further. "
            "I am happy to arrange a meeting at your convenience.\n\n"
            "Best regards,\n"
            "[Your Name]\n"
            "[Your Position]\n"
            "[Company Name]"
        ),
    }

    template = templates[tone].format(
        subject=subject.strip(), recipient=recipient_name
    )

    return {
        "success": True,
        "template": template,
        "tone": tone,
        "subject": subject,
    }


def proposal_template(
    title: str, context: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a proposal document template.

    Args:
        title: Proposal title.
        context: Brief context or background for the proposal.

    Returns:
        Dict with 'success' and 'template' string or 'error'.
    """
    if not title or not title.strip():
        return {"success": False, "error": "Proposal title cannot be empty."}

    context_text = context.strip() if context else "[Provide context here]"
    date_str = datetime.now().strftime("%B %d, %Y")

    template = (
        "=" * 60 + "\n"
        "PROPOSAL: {title}\n"
        "=" * 60 + "\n\n"
        "Date: {date}\n"
        "Prepared by: [Your Name]\n"
        "Organization: [Your Organization]\n\n"
        "-" * 40 + "\n"
        "1. EXECUTIVE SUMMARY\n"
        "-" * 40 + "\n\n"
        "[Provide a brief overview of the proposal in 2-3 sentences]\n\n"
        "-" * 40 + "\n"
        "2. BACKGROUND / CONTEXT\n"
        "-" * 40 + "\n\n"
        "{context}\n\n"
        "-" * 40 + "\n"
        "3. OBJECTIVES\n"
        "-" * 40 + "\n\n"
        "- Objective 1: [Description]\n"
        "- Objective 2: [Description]\n"
        "- Objective 3: [Description]\n\n"
        "-" * 40 + "\n"
        "4. PROPOSED SOLUTION / APPROACH\n"
        "-" * 40 + "\n\n"
        "[Describe your proposed approach in detail]\n\n"
        "4.1 Methodology\n"
        "[Explain your methodology]\n\n"
        "4.2 Timeline\n"
        "- Phase 1: [Timeline and deliverables]\n"
        "- Phase 2: [Timeline and deliverables]\n"
        "- Phase 3: [Timeline and deliverables]\n\n"
        "-" * 40 + "\n"
        "5. BUDGET / RESOURCES\n"
        "-" * 40 + "\n\n"
        "| Item          | Cost      | Notes          |\n"
        "|---------------|-----------|----------------|\n"
        "| [Item 1]      | [Cost]    | [Notes]        |\n"
        "| [Item 2]      | [Cost]    | [Notes]        |\n"
        "| Total         | [Total]   |                |\n\n"
        "-" * 40 + "\n"
        "6. EXPECTED OUTCOMES\n"
        "-" * 40 + "\n\n"
        "- [Expected outcome 1]\n"
        "- [Expected outcome 2]\n"
        "- [Expected outcome 3]\n\n"
        "-" * 40 + "\n"
        "7. CONCLUSION\n"
        "-" * 40 + "\n\n"
        "[Summarize the proposal and call to action]\n\n"
        "=" * 60 + "\n"
        "END OF PROPOSAL\n"
        "=" * 60 + "\n"
    ).format(title=title.strip(), date=date_str, context=context_text)

    return {
        "success": True,
        "template": template,
        "title": title,
    }


def caption_template(
    platform: str, topic: str
) -> Dict[str, Any]:
    """Generate a social media caption template.

    Args:
        platform: Social media platform ('instagram', 'twitter', 'linkedin',
                  'tiktok', 'facebook').
        topic: Topic or subject of the caption.

    Returns:
        Dict with 'success' and 'template' string or 'error'.
    """
    if not platform or not platform.strip():
        return {"success": False, "error": "Platform cannot be empty."}

    if not topic or not topic.strip():
        return {"success": False, "error": "Topic cannot be empty."}

    valid_platforms = ["instagram", "twitter", "linkedin", "tiktok", "facebook"]
    platform = platform.strip().lower()

    if platform not in valid_platforms:
        return {
            "success": False,
            "error": "Invalid platform '{}'. Valid: {}".format(
                platform, ", ".join(valid_platforms)
            ),
        }

    templates = {
        "instagram": (
            "[Hook - Attention-grabbing first line about {topic}]\n\n"
            "[Main content - 2-3 sentences about {topic}]\n\n"
            "[Call to action - Ask a question or invite engagement]\n\n"
            ".\n.\n.\n"
            "#[topic] #[related1] #[related2] #[related3] #[related4]\n"
            "#[niche] #[trending] #[community]"
        ),
        "twitter": (
            "[Concise take on {topic} - max 280 chars]\n\n"
            "[Optional thread continuation]\n\n"
            "#[Topic] #[Trending]"
        ),
        "linkedin": (
            "[Professional insight or story about {topic}]\n\n"
            "[Key takeaway or lesson learned]\n\n"
            "[Supporting details - 2-3 bullet points]:\n"
            "- Point 1\n"
            "- Point 2\n"
            "- Point 3\n\n"
            "[Call to action - invite discussion]\n\n"
            "#[Topic] #[Professional] #[Industry]"
        ),
        "tiktok": (
            "[Catchy hook for {topic}]\n\n"
            "[Brief description of the video content]\n\n"
            "[Trending sound suggestion: [sound name]]\n\n"
            "#[topic] #fyp #viral #[niche] #[trending]"
        ),
        "facebook": (
            "[Engaging opening about {topic}]\n\n"
            "[Story or detailed content - Facebook allows longer posts]\n\n"
            "[Personal touch or opinion]\n\n"
            "[Call to action - share, comment, or react]\n\n"
            "#[Topic] #[Related]"
        ),
    }

    template = templates[platform].format(topic=topic.strip())

    # Platform-specific tips
    tips = {
        "instagram": "Tip: Use 20-30 hashtags, post during peak hours (9am-11am, 7pm-9pm).",
        "twitter": "Tip: Keep under 280 chars, use 1-3 hashtags, engage with replies.",
        "linkedin": "Tip: Post on Tue-Thu mornings, use 3-5 hashtags, be professional.",
        "tiktok": "Tip: Use trending sounds, keep captions short, use 4-6 hashtags.",
        "facebook": "Tip: Longer posts perform well, ask questions, use 1-3 hashtags.",
    }

    return {
        "success": True,
        "template": template,
        "platform": platform,
        "topic": topic,
        "tip": tips[platform],
    }


def format_academic(text: str) -> Dict[str, Any]:
    """Format text in an academic/formal style.

    Applies academic formatting conventions: proper paragraph spacing,
    formal language indicators, and structural suggestions.

    Args:
        text: Text to format in academic style.

    Returns:
        Dict with 'success' and 'formatted' text or 'error'.
    """
    if not text or not text.strip():
        return {"success": False, "error": "Text cannot be empty."}

    text = text.strip()

    # Apply academic formatting rules
    # 1. Capitalize first letter of each sentence
    sentences = text.replace(". ", ".\n").split("\n")
    formatted_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            formatted_sentences.append(
                sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            )

    formatted = ". ".join(formatted_sentences)

    # Ensure proper ending punctuation
    if formatted and formatted[-1] not in ".!?":
        formatted += "."

    # Add academic structure suggestion
    structure = (
        "\n\n--- Academic Formatting Applied ---\n"
        "Structure suggestion:\n"
        "1. Introduction: State your thesis clearly\n"
        "2. Body: Support with evidence and citations\n"
        "3. Conclusion: Restate findings and implications\n"
        "\nFormatting notes:\n"
        "- Use passive voice where appropriate\n"
        "- Include in-text citations (Author, Year)\n"
        "- Maintain objective tone throughout\n"
        "- Use formal vocabulary and avoid contractions"
    )

    return {
        "success": True,
        "formatted": formatted,
        "original_length": len(text),
        "formatted_length": len(formatted),
        "style_guide": structure,
    }


def format_casual(text: str) -> Dict[str, Any]:
    """Format text in a casual/conversational style.

    Applies casual formatting: shorter sentences, conversational tone
    markers, and readability improvements.

    Args:
        text: Text to format in casual style.

    Returns:
        Dict with 'success' and 'formatted' text or 'error'.
    """
    if not text or not text.strip():
        return {"success": False, "error": "Text cannot be empty."}

    text = text.strip()

    # Apply casual formatting
    # Replace formal phrases with casual equivalents
    casual_replacements = [
        ("In conclusion,", "So basically,"),
        ("Furthermore,", "Also,"),
        ("Nevertheless,", "But still,"),
        ("In addition,", "Plus,"),
        ("However,", "But,"),
        ("Therefore,", "So,"),
        ("Moreover,", "And also,"),
        ("Consequently,", "Because of that,"),
        ("Subsequently,", "Then,"),
        ("Notwithstanding,", "Even so,"),
        ("In accordance with", "According to"),
        ("With regard to", "About"),
        ("It is important to note that", "Just so you know,"),
        ("It should be noted that", "BTW,"),
    ]

    formatted = text
    for formal, casual in casual_replacements:
        formatted = formatted.replace(formal, casual)
        formatted = formatted.replace(formal.lower(), casual.lower())

    # Add casual formatting tips
    style_tips = (
        "\n\n--- Casual Formatting Applied ---\n"
        "Style tips for casual writing:\n"
        "- Keep sentences short and punchy\n"
        "- Use contractions (don't, won't, it's)\n"
        "- Add personal pronouns (I, you, we)\n"
        "- Use everyday vocabulary\n"
        "- It's okay to start sentences with 'And' or 'But'\n"
        "- Add personality and humor where appropriate"
    )

    return {
        "success": True,
        "formatted": formatted,
        "original_length": len(text),
        "formatted_length": len(formatted),
        "style_guide": style_tips,
    }
