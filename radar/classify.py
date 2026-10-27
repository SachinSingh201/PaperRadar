"""Topic and organization classification based on keyword matching."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem

logger = logging.getLogger("radar.classify")

KNOWN_ORGS: Dict[str, List[str]] = {
    "Google DeepMind": ["deepmind", "google deepmind"],
    "Google Research": ["google research", "google ai"],
    "OpenAI": ["openai", "gpt-4", "chatgpt"],
    "Anthropic": ["anthropic", "claude"],
    "Meta AI": ["meta ai", "fair", "llama"],
    "Microsoft Research": ["microsoft research", "microsoft ai"],
    "NVIDIA": ["nvidia research", "nvidia"],
    "Apple": ["apple research", "apple machine learning"],
    "Stanford": ["stanford", "stanford hai", "crfm"],
    "MIT CSAIL": ["mit csail", "massachusetts institute of technology"],
    "UC Berkeley": ["bair", "berkeley artificial intelligence"],
    "CMU": ["carnegie mellon", "cmu"],
    "Allen Institute (AI2)": ["allen institute for ai", "ai2", "allenai"],
    "Hugging Face": ["hugging face", "huggingface"],
    "Mistral AI": ["mistral ai", "mistral"],
    "Cohere": ["cohere", "cohere for ai"],
    "Tsinghua": ["tsinghua university", "tsinghua"],
}


class Classifier:
    """Classifies research items into topic categories and extracts organization affiliations."""

    def __init__(self, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.topics = self.config.topics  # dict: topic -> list of keywords
        self._compiled_regexes: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compiles regex patterns for efficient topic matching."""
        for topic, keywords in self.topics.items():
            patterns = []
            for kw in keywords:
                escaped = re.escape(kw)
                # Word boundary match
                pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
                patterns.append(pattern)
            self._compiled_regexes[topic] = patterns

    def classify_item(self, item: RadarItem) -> Tuple[List[str], float]:
        """Assigns topic tags and computes a normalized topic match score (0.0 to 1.0).

        Returns:
            Tuple of (assigned_topics: list of strings, topic_score: float)
        """
        text_corpus = f"{item.title} {item.title} {item.abstract}".lower()
        matched_topics: List[str] = []
        total_hits = 0

        for topic, patterns in self._compiled_regexes.items():
            topic_hits = 0
            for pattern in patterns:
                # Count matches
                matches = pattern.findall(text_corpus)
                if matches:
                    topic_hits += len(matches)

            if topic_hits > 0:
                matched_topics.append(topic)
                total_hits += topic_hits

        # Inferred organization if missing
        if not item.org:
            inferred_org = self.infer_org(text_corpus)
            if inferred_org:
                item.org = inferred_org

        # Set comma-separated string
        if matched_topics:
            item.topics = ",".join(matched_topics)

        # Compute normalized topic score (clamped between 0.1 and 1.0)
        if not matched_topics:
            topic_score = 0.1
        else:
            # Diminishing returns formula
            topic_score = min(1.0, 0.3 + (total_hits * 0.15))

        return matched_topics, topic_score

    def infer_org(self, text: str) -> str:
        """Infers organization from authors/text if identifiable."""
        for org, patterns in KNOWN_ORGS.items():
            for p in patterns:
                if re.search(rf"\b{re.escape(p)}\b", text, re.IGNORECASE):
                    return org
        return ""
