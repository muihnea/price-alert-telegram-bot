import re
import sys
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ro;q=0.8",
}


def parse_price(text: str) -> float:
    """Turn '1.299,99 Lei', '$1,299.99' or '51.77' into a float."""
    match = re.search(r"\d[\d.,\s]*", text)
    if not match:
        raise ValueError("No number found")
    s = match.group().strip().replace(" ", "")
    s = s.rstrip(".,")

    if "." in s and "," in s:
        # the last separator is the decimal one
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if re.search(r",\d{1,2}$", s):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s:
        if s.count(".") > 1 or re.search(r"\.\d{3}$", s):
            s = s.replace(".", "")
    return float(s)


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def from_json_ld(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _walk(data):
            offers = node.get("offers")
            if offers is None:
                continue
            for offer in offers if isinstance(offers, list) else [offers]:
                if not isinstance(offer, dict):
                    continue
                for key in ("price", "lowPrice"):
                    if offer.get(key) not in (None, ""):
                        return parse_price(str(offer[key]))
    return None


def from_meta(soup):
    for prop in ("product:price:amount", "og:price:amount"):
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            return parse_price(tag["content"])
    return None


def from_itemprop(soup):
    tag = soup.find(attrs={"itemprop": "price"})
    if tag:
        return parse_price(tag.get("content") or tag.get_text())
    return None


def from_css(soup):
    tag = soup.select_one("p.price_color")  # books.toscrape.com
    if tag:
        return parse_price(tag.get_text())
    return None


def get_price(url: str) -> float:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for method in (from_json_ld, from_meta, from_itemprop, from_css):
        try:
            price = method(soup)
        except ValueError:
            continue
        if price is not None:
            return price

    raise ValueError("Price not found on this page")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else (
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    print(get_price(url))