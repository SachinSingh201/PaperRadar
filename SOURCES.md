# Paper Radar — Verified Sources & Terms of Use

This document lists every active source indexed by **Paper Radar**, its retrieval method, publisher organization, authority tier, and official terms of service link.

Paper Radar adheres strictly to ethical aggregation principles:
- **Feeds and official APIs first**; no aggressive or unauthorized scraping.
- Full compliance with `robots.txt` (checked and cached for 24 hours).
- Strict rate limiting: minimum 3.0 seconds between requests per domain.
- Metadata and factual summaries only; no mirroring of full paper PDFs or paywalled articles.
- Clear attribution and backlink to original source URLs on every item.

---

| Source Name | Organization | Content Type | Retrieval Method | Authority Tier | Official Terms Link |
|---|---|---|---|---|---|
| **arXiv Computer Science & AI** | arXiv / Cornell | Papers | Official Atom Query API | Tier 1 | [arXiv Terms of Use](https://arxiv.org/help/api/tou) |
| **Hugging Face Daily Papers** | Hugging Face | Papers | Official REST API | Tier 1 | [HF Terms of Service](https://huggingface.co/terms-of-service) |
| **Google DeepMind Research** | Google DeepMind | Lab Blog / Releases | Official RSS Feed | Tier 1 | [Google Terms](https://policies.google.com/terms) |
| **Google Research Blog** | Google Research | Lab Blog | Official RSS Feed | Tier 1 | [Google Terms](https://policies.google.com/terms) |
| **OpenAI News & Research** | OpenAI | Lab Blog / Releases | Official RSS Feed | Tier 1 | [OpenAI Terms of Use](https://openai.com/policies/terms-of-use/) |
| **Anthropic News & Announcements** | Anthropic | Lab Blog / Releases | Official RSS Feed | Tier 1 | [Anthropic Consumer Terms](https://www.anthropic.com/legal/consumer-terms) |
| **Microsoft Research Blog** | Microsoft Research | Lab Blog | Official RSS Feed | Tier 1 | [Microsoft Terms of Use](https://www.microsoft.com/en-us/legal/terms-of-use) |
| **NVIDIA Research Blog** | NVIDIA | Lab Blog | Official RSS Feed | Tier 1 | [NVIDIA Legal Info](https://www.nvidia.com/en-us/about-nvidia/legal-info/) |
| **Apple Machine Learning Research** | Apple | Lab Blog | Official RSS Feed | Tier 1 | [Apple Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) |
| **Hugging Face Blog** | Hugging Face | Lab Blog | Official RSS Feed | Tier 1 | [HF Terms of Service](https://huggingface.co/terms-of-service) |
| **Cohere AI Blog** | Cohere | Lab Blog | Official RSS Feed | Tier 2 | [Cohere Terms of Use](https://cohere.com/terms-of-use) |
| **LangChain Official Blog** | LangChain | Lab Blog | Official RSS Feed | Tier 2 | [LangChain Terms](https://www.langchain.com/terms-of-service) |
| **LlamaIndex Official Blog** | LlamaIndex | Lab Blog | Official RSS Feed | Tier 2 | [LlamaIndex Terms](https://www.llamaindex.ai/terms) |
| **Stanford HAI** | Stanford University | Institute News | Official RSS Feed | Tier 1 | [Stanford Site Terms](https://www.stanford.edu/site/terms/) |
| **MIT CSAIL** | MIT CSAIL | Institute News | Official RSS Feed | Tier 1 | [MIT Reference Terms](https://web.mit.edu/reference/terms.html) |
| **Berkeley AI Research (BAIR)** | UC Berkeley | Institute Blog | Official RSS Feed | Tier 1 | [BAIR Site](https://bair.berkeley.edu/) |
| **Allen Institute for AI (AI2)** | AI2 | Institute Blog | Official RSS Feed | Tier 1 | [AI2 Terms of Use](https://allenai.org/terms) |
| **Model Context Protocol (MCP) Spec** | Anthropic / MCP Working Group | Protocol Specs | GitHub Releases Atom Feed | Tier 1 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| **vLLM Inference Engine** | vLLM Team | Open Source Releases | GitHub Releases Atom Feed | Tier 1 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| **llama.cpp Engine** | Georgi Gerganov / llama.cpp | Open Source Releases | GitHub Releases Atom Feed | Tier 1 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| **Ollama Model Runtime** | Ollama | Open Source Releases | GitHub Releases Atom Feed | Tier 1 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| **Hugging Face Transformers** | Hugging Face | Open Source Releases | GitHub Releases Atom Feed | Tier 1 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |
| **LangChain Core Releases** | LangChain | Open Source Releases | GitHub Releases Atom Feed | Tier 2 | [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) |

---

## Modifying or Adding Sources
To add or modify sources, update `config/sources.yaml`. Ensure that:
1. The domain is registered under the allowlist.
2. The URL points to an official public feed or API.
3. The publisher's `robots.txt` does not disallow the feed path.
