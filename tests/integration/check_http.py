"""Exercise Plain Log through a real WordPress HTTP server."""

import re
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, url):
        return None


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_navigation = False
        self.current_href = None
        self.current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "nav" and "page-links" in attributes.get("class", "").split():
            self.in_navigation = True
        elif self.in_navigation and tag == "a":
            self.current_href = attributes.get("href")
            self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href is not None:
            self.links.append((self.current_href, "".join(self.current_text).strip()))
            self.current_href = None
        elif tag == "nav" and self.in_navigation:
            self.in_navigation = False


site_url, post_url, page_url = sys.argv[1:]
site_origin = urlsplit(site_url).netloc
opener = build_opener(NoRedirect)


def fetch(label, url, expected_status=200):
    if urlsplit(url).netloc != site_origin:
        raise AssertionError(f"{label}: URL escaped the test site: {url}")
    request = Request(url, headers={"User-Agent": "PlainLogIntegrationCI/1"})
    try:
        response = opener.open(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        status = response.status
        body = response.read().decode("utf-8", errors="replace")
    if status != expected_status:
        raise AssertionError(f"{label}: expected HTTP {expected_status}, got {status}: {url}")
    print(f"PASS {label}: HTTP {status}")
    return body


def contains(label, body, text):
    if text not in body:
        raise AssertionError(f"{label}: missing {text!r}")


def excludes(label, body, text):
    if text in body:
        raise AssertionError(f"{label}: unexpectedly found {text!r}")


def check_pagination(label, url, title, first_marker, second_marker):
    first = fetch(f"{label} page 1", url)
    contains(label, first, title)
    contains(label, first, first_marker)
    excludes(label, first, second_marker)
    links = PageLinks()
    links.feed(first)
    second_links = [href for href, text in links.links if re.search(r"\b2\b", text)]
    if len(second_links) != 1:
        raise AssertionError(f"{label}: expected one page 2 navigation link, got {links.links!r}")
    second_url = urljoin(url, second_links[0])
    second = fetch(f"{label} page 2", second_url)
    contains(label, second, title)
    contains(label, second, second_marker)
    excludes(label, second, first_marker)


home = fetch("home", site_url + "/")
contains("home", home, "home-index")
contains("home", home, "CIUniqueTokenAlpha article")

check_pagination("post", post_url, "CIUniqueTokenAlpha article", "CI_POST_FIRST_PAGE", "CI_POST_SECOND_PAGE")
check_pagination("page", page_url, "CI paginated page", "CI_PAGE_FIRST_PAGE", "CI_PAGE_SECOND_PAGE")

search = fetch("search", site_url + "/?s=CIUniqueTokenAlpha")
contains("search", search, "search-results-index")
contains("search", search, "CIUniqueTokenAlpha article")
excludes("search", search, "CI paginated page")

missing = fetch("404", site_url + "/?p=999999999", expected_status=404)
contains("404", missing, "Page not found.")

print("WordPress integration checks passed.")
