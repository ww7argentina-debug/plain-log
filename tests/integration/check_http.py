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
        self.found_navigation = False
        self.in_navigation = False
        self.current_href = None
        self.current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "nav" and "page-links" in attributes.get("class", "").split():
            self.found_navigation = True
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


mode = sys.argv[1] if sys.argv[1] in ("--plain-index", "--protected-index") else "paginated"
if mode == "paginated":
    site_url, post_url, page_url, categories_url, tags_url = sys.argv[1:]
else:
    site_url, categories_url, tags_url = sys.argv[2:]
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


def main_content(label, body):
    match = re.search(r"<main\b[^>]*>(.*?)</main>", body, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"{label}: missing main content")
    return match.group(1)


def class_content(label, body, tag, class_name):
    pattern = rf'<{tag}\b[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>(.*?)</{tag}>'
    match = re.search(pattern, body, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"{label}: missing {class_name}")
    return match.group(1)


def index_content(label, body, title, term_name):
    main = main_content(label, body)
    contains(label, main, "taxonomy-index-page")
    contains(label, main, title)
    section = class_content(label, main, "section", "taxonomy-index")
    term_pattern = rf'<li class="taxonomy-index-item">\s*<a\b[^>]*>{re.escape(term_name)}</a>\s*<span class="taxonomy-index-count">1</span>'
    if re.search(term_pattern, section) is None:
        raise AssertionError(f"{label}: missing indexed term and count: {term_name}; section={section.strip()[:600]!r}")
    return main


def check_index_pagination(label, url, title, term_name, markers):
    current_url = url
    for page_number, marker in enumerate(markers, start=1):
        page_label = f"{label} page {page_number}"
        body = fetch(page_label, current_url)
        main = index_content(page_label, body, title, term_name)
        entry = class_content(page_label, main, "div", "entry-content")
        for page_marker in markers:
            if page_marker is not None:
                (contains if page_marker == marker else excludes)(page_label, entry, page_marker)
        links = PageLinks()
        links.feed(entry)
        if not links.found_navigation:
            raise AssertionError(f"{page_label}: missing page navigation")
        if page_number < len(markers):
            next_links = [href for href, text in links.links if re.search(rf"\b{page_number + 1}\b", text)]
            if len(next_links) != 1:
                raise AssertionError(f"{page_label}: expected one page {page_number + 1} link, got {links.links!r}")
            current_url = urljoin(url, next_links[0])


def check_plain_index(label, url, title, term_name, marker):
    body = fetch(label, url)
    main = index_content(label, body, title, term_name)
    entry = class_content(label, main, "div", "entry-content")
    contains(label, entry, marker)
    links = PageLinks()
    links.feed(entry)
    if links.found_navigation:
        raise AssertionError(f"{label}: unexpected page navigation")


def check_protected_index(label, url, title, term_name, markers):
    body = fetch(label, url)
    main = index_content(label, body, title, term_name)
    contains(label, main, 'type="password"')
    for marker in markers:
        excludes(label, body, marker)


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


if mode == "paginated":
    home = fetch("home", site_url + "/")
    contains("home", home, "home-index")
    contains("home", home, "CIUniqueTokenAlpha article")

    check_pagination("post", post_url, "CIUniqueTokenAlpha article", "CI_POST_FIRST_PAGE", "CI_POST_SECOND_PAGE")
    check_pagination("page", page_url, "CI paginated page", "CI_PAGE_FIRST_PAGE", "CI_PAGE_SECOND_PAGE")

    search = fetch("search", site_url + "/?s=CIUniqueTokenAlpha")
    contains("search", search, "search-results-index")
    contains("search", search, "CIUniqueTokenAlpha article")
    excludes("search results", main_content("search", search), "CI paginated page")

    missing = fetch("404", site_url + "/?p=999999999", expected_status=404)
    contains("404", missing, "Page not found.")

    failures = []
    for args in (
        ("categories index", categories_url, "CI Categories index", "CI Category Alpha", (None, "CI_CATEGORY_PAGE_TWO")),
        ("tags index", tags_url, "CI Tags index", "CI Tag Alpha", ("CI_TAG_PAGE_ONE", None, "CI_TAG_PAGE_THREE")),
    ):
        try:
            check_index_pagination(*args)
        except AssertionError as error:
            failures.append(str(error))
    if failures:
        raise AssertionError("\n".join(failures))
elif mode == "--plain-index":
    check_plain_index("categories plain index", categories_url, "CI Categories index", "CI Category Alpha", "CI_CATEGORY_PLAIN_CONTENT")
    check_plain_index("tags plain index", tags_url, "CI Tags index", "CI Tag Alpha", "CI_TAG_PLAIN_CONTENT")
else:
    check_protected_index("categories protected index", categories_url, "CI Categories index", "CI Category Alpha", ("CI_CATEGORY_SECRET_ONE", "CI_CATEGORY_SECRET_TWO"))
    check_protected_index("tags protected index", tags_url, "CI Tags index", "CI Tag Alpha", ("CI_TAG_SECRET_ONE", "CI_TAG_SECRET_TWO"))

print("WordPress integration checks passed.")
