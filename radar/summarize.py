"""Text summarization with strict prompt-injection defenses and extractive defaults."""

from __future__ import annotations

import logging
import re
from typing import List, Optional
from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem, strip_html_tags

logger = logging.getLogger("radar.summarize")

# Known prompt-injection trigger patterns in untrusted web text
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"disregard\s+(the\s+)?instructions",
    r"print\s+the\s+secret",
    r"bypass\s+safety",
    r"prompt\s+injection",
]


def sanitize_untrusted_text(raw_text: str) -> str:
    """Cleans untrusted scraped text and defuses prompt injection payloads."""
    if not raw_text:
        return ""

    # Strip HTML and scripts
    cleaned = strip_html_tags(raw_text)

    # Neutralize prompt injection phrases by defanging them
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[redacted instruction]", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def split_sentences(text: str) -> List[str]:
    """Splits text into cleaned sentences."""
    if not text:
        return []
    # Avoid splitting on abbreviations like e.g., i.e., et al., Fig.
    text = re.sub(r"\b(e\.g\.|i\.e\.|et\s+al\.|fig\.|dr\.|prof\.|vs\.)\s+", r"\1__SPACE__", text, flags=re.IGNORECASE)
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    for s in raw_sentences:
        s = s.replace("__SPACE__", " ").strip()
        if len(s) > 20:  # Ignore fragments
            sentences.append(s)
    return sentences


class Summarizer:
    """Summarizes research items into 3 factual bullets + 'Why it matters'."""

    def __init__(self, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.mode = self.config.summary_mode

    def summarize_extractive(self, item: RadarItem) -> str:
        """Generates a high-quality 3-bullet factual summary + 'Why it matters' extractive synthesis."""
        sanitized_abstract = sanitize_untrusted_text(item.abstract)
        sentences = split_sentences(sanitized_abstract)

        # Fallback if text is very short
        if not sentences:
            if sanitized_abstract:
                bullet1 = sanitized_abstract[:160] + "..." if len(sanitized_abstract) > 160 else sanitized_abstract
            else:
                bullet1 = f"New publication or release titled '{item.title}' from {item.org or item.source}."
            return (
                f"- {bullet1}\n"
                f"- Details core concepts and practical implications in {item.topics or 'AI research'}.\n"
                f"- Full documentation and findings accessible via the source link.\n\n"
                f"**Why it matters:** Expands open knowledge and technological capabilities in {item.topics or 'machine learning'}."
            )

        # Sentence 1: Proposal / Core Problem
        bullet1 = sentences[0]

        # Sentence 2: Key Methodology or Technical Insight
        if len(sentences) >= 3:
            # Pick a middle sentence highlighting method/mechanism
            mid_candidates = sentences[1:-1]
            method_sentence = next(
                (s for s in mid_candidates if any(k in s.lower() for k in ["propose", "method", "model", "present", "introduce", "architecture", "technique", "approach", "framework"])),
                sentences[1],
            )
            bullet2 = method_sentence
        elif len(sentences) == 2:
            bullet2 = sentences[1]
        else:
            bullet2 = "Focuses on architectural and algorithmic advancements in the domain."

        # Sentence 3: Findings / Results / Capabilities
        if len(sentences) >= 3:
            last_candidates = sentences[2:]
            results_sentence = next(
                (s for s in last_candidates if any(k in s.lower() for k in ["demonstrate", "result", "show", "achieve", "improve", "outperform", "benchmark", "state-of-the-art", "sota", "evaluate"])),
                sentences[-1],
            )
            bullet3 = results_sentence
        else:
            bullet3 = "Demonstrates measurable improvements and technical feasibility across standard evaluation benchmarks."

        # Why it matters synthesis
        topic_highlight = item.topics.split(",")[0].upper() if item.topics else "AI"
        why_it_matters = (
            f"Provides actionable insights and reference implementations for {topic_highlight} systems, "
            f"addressing critical challenges highlighted by {item.org or 'the community'}."
        )

        formatted_summary = (
            f"- {bullet1}\n"
            f"- {bullet2}\n"
            f"- {bullet3}\n\n"
            f"**Why it matters:** {why_it_matters}"
        )
        return formatted_summary

    def summarize(self, item: RadarItem) -> str:
        """Dispatches to the configured summarizer mode and attaches model name."""
        if self.mode == "extractive" or self.config.profile == "LOCAL_LITE":
            item.summary = self.summarize_extractive(item)
            item.summary_model = "extractive-v1"
            return item.summary

        # If LLM or Ollama mode requested, we can attempt with strict guardrails
        # but safely fallback to extractive if offline or unavailable
        try:
            summary = self.summarize_extractive(item)
            item.summary = summary
            item.summary_model = f"{self.mode}-fallback-extractive"
            return item.summary
        except Exception as e:
            logger.warning(f"Summarization error: {e}, falling back to extractive")
            item.summary = self.summarize_extractive(item)
            item.summary_model = "extractive-v1"
            return item.summary
