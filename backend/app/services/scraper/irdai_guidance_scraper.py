"""
IRDAI Consumer Guidance and Regulatory Scraper.

Collects:
1. Standard Health Product Guidelines & FAQs (Arogya Sanjeevani, Saral Suraksha Bima)
2. IRDAI Health Department circulars and disclosures
3. Registered Health & General Insurers master directory from IRDAI
"""
import os
import re
import json
import time
import logging
import urllib.request
import ssl
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger("bimagyan.scraper.irdai_guidance")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

GUIDANCE_TARGETS = [
    {
        "topic": "Arogya Sanjeevani Standard Health Policy",
        "category": "Standard Products",
        "url": "https://irdai.gov.in/faq-s-on-standard-health-product-arogya-sanjeevani-product",
        "description": "IRDAI-mandated standard health insurance product across all general and standalone insurers."
    },
    {
        "topic": "Saral Suraksha Bima Standard Personal Accident Product",
        "category": "Standard Products",
        "url": "https://irdai.gov.in/faqs-on-guidelines-on-standard-personal-accident-insurance-product-saral-suraksha-bima",
        "description": "IRDAI-mandated standard individual personal accident policy."
    },
    {
        "topic": "List of Health Insurers",
        "category": "Registered Entities",
        "url": "https://irdai.gov.in/list-of-health-insurers",
        "description": "Official IRDAI directory of standalone health insurance companies operating in India."
    },
    {
        "topic": "List of General Insurers",
        "category": "Registered Entities",
        "url": "https://irdai.gov.in/list-of-general-insurers",
        "description": "Official IRDAI directory of non-life and general insurance companies in India."
    }
]


class IRDAIGuidanceScraper:
    def __init__(self, output_dir: str = "data/scraped/regulations"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.ssl_ctx = ssl.create_default_context()

    def fetch_url(self, url: str) -> Optional[str]:
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=20) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error("Error fetching %s: %s", url, e)
        return None

    def parse_faqs_or_articles(self, html: str, url: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # 1. First look for Bootstrap Accordion / Card patterns (standard in IRDAI Liferay theme)
        cards = soup.find_all(class_=lambda c: c and "card" in str(c).lower())
        for c in cards:
            header = c.find(class_=lambda x: x and ("header" in str(x).lower() or "btn" in str(x).lower()))
            body = c.find(class_=lambda x: x and "body" in str(x).lower())
            if header and body:
                q = header.get_text(" ", strip=True)
                a = body.get_text(" ", strip=True)
                if len(q) > 5 and len(a) > 5:
                    items.append({
                        "question": q,
                        "answer": a,
                        "source_url": url
                    })

        if items:
            return items

        # 2. Fallback to paragraph sequence analysis
        article_div = soup.find(class_=lambda c: c and any(k in str(c).lower() for k in ["journal-content-article", "portlet-body", "content"]))
        if not article_div:
            article_div = soup.find("main") or soup.find("body")

        elements = article_div.find_all(["p", "h2", "h3", "h4", "li"])
        current_question = None
        current_answers = []

        for el in elements:
            text = el.get_text(" ", strip=True)
            if not text or len(text) < 10:
                continue

            is_question = bool(
                text.endswith("?") or 
                re.match(r"^(?:Q(?:uestion)?\.?\s*\d+|[0-9]{1,2}[\.\)])\s+", text) or
                el.name in ["h2", "h3", "h4"] or
                any(text.lower().startswith(w) for w in ["what ", "how ", "can ", "whether ", "who ", "which ", "is "])
            )

            if is_question:
                if current_question and current_answers:
                    items.append({
                        "question": current_question,
                        "answer": " ".join(current_answers),
                        "source_url": url
                    })
                    current_answers = []
                current_question = text
            else:
                if current_question:
                    current_answers.append(text)

        if current_question and current_answers:
            items.append({
                "question": current_question,
                "answer": " ".join(current_answers),
                "source_url": url
            })

        return items

    def parse_table_directory(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        if not rows:
            return []

        headers = [th.get_text(" ", strip=True) for th in rows[0].find_all(["th", "td"])]
        entities = []
        for r in rows[1:]:
            tds = [td.get_text(" ", strip=True) for td in r.find_all("td")]
            if len(tds) >= 2:
                row_dict = {}
                for idx, val in enumerate(tds):
                    key = headers[idx] if idx < len(headers) else f"col_{idx}"
                    row_dict[key] = val
                # Check for website link
                a_tag = r.find("a", href=True)
                if a_tag:
                    row_dict["website_url"] = a_tag["href"]
                entities.append(row_dict)

        return entities

    def scrape_all(self) -> Dict[str, Any]:
        all_results = {
            "faqs_and_guidelines": [],
            "registered_insurers": [],
            "source_urls": [],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        for target in GUIDANCE_TARGETS:
            logger.info("Fetching IRDAI Guidance: %s (%s)...", target["topic"], target["url"])
            html = self.fetch_url(target["url"])
            if not html:
                continue

            all_results["source_urls"].append(target["url"])

            if "list-of" in target["url"]:
                entities = self.parse_table_directory(html, target["url"])
                for e in entities:
                    e["entity_category"] = target["topic"]
                    all_results["registered_insurers"].append(e)
                logger.info("  Parsed %d registered entities from %s", len(entities), target["topic"])
            else:
                faqs = self.parse_faqs_or_articles(html, target["url"])
                for f in faqs:
                    f["topic"] = target["topic"]
                    f["category"] = target["category"]
                    all_results["faqs_and_guidelines"].append(f)
                logger.info("  Parsed %d Q&As/guidelines from %s", len(faqs), target["topic"])

            time.sleep(1.2)

        # Save to JSON
        output_path = os.path.join(self.output_dir, "irdai_health_guidance.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        logger.info(
            "IRDAI Guidance scraped successfully: %d Q&As, %d registered insurers saved to %s",
            len(all_results["faqs_and_guidelines"]),
            len(all_results["registered_insurers"]),
            output_path
        )
        return all_results


if __name__ == "__main__":
    scraper = IRDAIGuidanceScraper()
    scraper.scrape_all()
