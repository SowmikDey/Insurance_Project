"""
IRDAI Product Catalogue Scraper.

Fetches approved health insurance products from the official IRDAI portal:
URL: https://irdai.gov.in/health-insurance-products

Extracts:
- UIN (Unique Identification Number)
- Product Name
- Insurer Name
- Financial Year
- Date of Approval
- Product Type (Individual, Group, Add on, Revision, etc.)
- Archive / Non-Archive status
- Direct PDF Download link and file size
"""
import os
import re
import json
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import urllib.request
import ssl
from bs4 import BeautifulSoup

logger = logging.getLogger("bimagyan.scraper.irdai")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_CATALOGUE_URL = "https://irdai.gov.in/health-insurance-products"
PAGINATION_URL_TEMPLATE = (
    "https://irdai.gov.in/health-insurance-products?"
    "p_p_id=com_irdai_document_media_IRDAIDocumentMediaPortlet"
    "&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view"
    "&_com_irdai_document_media_IRDAIDocumentMediaPortlet_delta=20"
    "&_com_irdai_document_media_IRDAIDocumentMediaPortlet_resetCur=false"
    "&_com_irdai_document_media_IRDAIDocumentMediaPortlet_cur={page_num}"
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class IRDAICatalogueScraper:
    def __init__(self, output_dir: str = "data/scraped/catalogue"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.ssl_ctx = ssl.create_default_context()

    def fetch_page_html(self, page_num: int = 1, timeout: int = 25) -> Optional[str]:
        """Fetches the HTML for a given page number with retry."""
        url = BASE_CATALOGUE_URL if page_num == 1 else PAGINATION_URL_TEMPLATE.format(page_num=page_num)
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=timeout) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="ignore")
                    logger.warning("Attempt %d: HTTP %d for page %d", attempt, resp.status, page_num)
            except Exception as e:
                logger.warning("Attempt %d failed for page %d: %s", attempt, page_num, e)
                time.sleep(2 * attempt)
        return None

    def parse_catalogue_table(self, html: str) -> List[Dict[str, Any]]:
        """Parses the products table from the IRDAI HTML page."""
        soup = BeautifulSoup(html, "html.parser")
        tbl = soup.find("table")
        if not tbl:
            logger.error("No table found in IRDAI page HTML.")
            return []

        rows = tbl.find_all("tr")
        if not rows:
            return []

        products = []
        for r in rows[1:]:  # skip header row
            tds = r.find_all("td")
            if len(tds) < 8:
                continue

            # Column structure:
            # tds[0]: Checkbox/Empty
            # tds[1]: Archive / Non Archive
            # tds[2]: Financial Year
            # tds[3]: Name of the Insurer
            # tds[4]: UIN
            # tds[5]: Product Name
            # tds[6]: Date of Approval
            # tds[7]: Documents (with link)
            # tds[8]: Type Of Product (if present)

            archive_status = tds[1].get_text(strip=True) if len(tds) > 1 else "Non-Archived"
            financial_year = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            insurer_name = tds[3].get_text(" ", strip=True) if len(tds) > 3 else ""
            uin = tds[4].get_text(strip=True) if len(tds) > 4 else ""
            product_name = tds[5].get_text(" ", strip=True) if len(tds) > 5 else ""
            approval_date = tds[6].get_text(strip=True) if len(tds) > 6 else ""

            doc_cell = tds[7] if len(tds) > 7 else None
            doc_link = None
            doc_filename = ""
            doc_filesize = ""
            if doc_cell:
                a_tag = doc_cell.find("a", href=True)
                if a_tag:
                    doc_link = a_tag["href"].strip()
                    if not doc_link.startswith("http"):
                        doc_link = urljoin(BASE_CATALOGUE_URL, doc_link)
                cell_text = doc_cell.get_text(" ", strip=True)
                # extract filesize like '1.3 MB' or '115 KB'
                size_match = re.search(r"(\d+(?:\.\d+)?\s*(?:KB|MB|GB|Bytes))", cell_text, re.IGNORECASE)
                if size_match:
                    doc_filesize = size_match.group(1)
                file_match = re.search(r"([A-Za-z0-9_\-\.]+\.pdf)", cell_text, re.IGNORECASE)
                if file_match:
                    doc_filename = file_match.group(1)

            product_type = tds[8].get_text(strip=True) if len(tds) > 8 else "Health"

            if uin or product_name:
                product_data = {
                    "uin": uin,
                    "product_name": product_name,
                    "insurer_name": insurer_name,
                    "financial_year": financial_year,
                    "approval_date": approval_date,
                    "product_type": product_type,
                    "archive_status": archive_status,
                    "document_url": doc_link,
                    "document_filename": doc_filename,
                    "document_filesize": doc_filesize,
                    "source_portal": "IRDAI Health Insurance Product Catalogue",
                    "catalogue_page_url": BASE_CATALOGUE_URL,
                }
                products.append(product_data)

        return products

    def scrape(self, max_pages: int = 5, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Scrapes pages from start_page up to max_pages.
        Saves output directly to JSON and JSONL.
        """
        all_products = []
        seen_uins = set()

        logger.info("Starting IRDAI catalogue scrape from page %d (max pages: %d)...", start_page, max_pages)

        for p in range(start_page, start_page + max_pages):
            logger.info("Fetching IRDAI catalogue page %d...", p)
            html = self.fetch_page_html(p)
            if not html:
                logger.warning("Stopping: Could not fetch page %d", p)
                break

            items = self.parse_catalogue_table(html)
            if not items:
                logger.info("No items found on page %d, ending scrape.", p)
                break

            new_items = 0
            for item in items:
                uin = item.get("uin")
                if uin and uin in seen_uins:
                    continue
                if uin:
                    seen_uins.add(uin)
                all_products.append(item)
                new_items += 1

            logger.info("Page %d parsed: %d items (%d new). Total collected so far: %d", p, len(items), new_items, len(all_products))
            time.sleep(1.2)  # Polite crawl rate limit

        # Save to JSON
        json_path = os.path.join(self.output_dir, "irdai_products.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)

        # Save to JSONL for streaming/batch consumption
        jsonl_path = os.path.join(self.output_dir, "irdai_products.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in all_products:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Save summary
        insurers = sorted(list(set(p["insurer_name"] for p in all_products if p.get("insurer_name"))))
        types = sorted(list(set(p["product_type"] for p in all_products if p.get("product_type"))))
        summary = {
            "total_products_scraped": len(all_products),
            "pages_scraped": max_pages,
            "unique_insurers_count": len(insurers),
            "insurers_list": insurers,
            "product_types": types,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(os.path.join(self.output_dir, "irdai_catalogue_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("Successfully scraped %d products across %d insurers! Saved to %s", len(all_products), len(insurers), json_path)
        return all_products


if __name__ == "__main__":
    scraper = IRDAICatalogueScraper()
    scraper.scrape(max_pages=3)
