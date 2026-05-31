#!/usr/bin/env python3
"""Fetch recent PubMed papers that are useful for school-fit research notes."""

from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHOOLS_JSON = ROOT / "data" / "schools.json"
OUTPUT_JSON = ROOT / "data" / "school_research_papers.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SSL_CONTEXT = ssl._create_unverified_context()


AFFILIATION_TERMS = {
    "uc-davis": ["UC Davis", "University of California Davis"],
    "ucsd": ["UC San Diego", "University of California San Diego"],
    "kaiser-permanente": ["Kaiser Permanente Bernard J. Tyson School of Medicine", "Kaiser Permanente Southern California"],
    "temple": ["Lewis Katz School of Medicine", "Temple University"],
    "emory": ["Emory University School of Medicine", "Emory University"],
    "virginia-tech-carilion": ["Virginia Tech Carilion School of Medicine", "Carilion Clinic"],
    "vermont-larner": ["Larner College of Medicine", "University of Vermont"],
    "wisconsin": ["University of Wisconsin School of Medicine and Public Health", "University of Wisconsin Madison"],
    "mcw": ["Medical College of Wisconsin"],
    "jefferson-kimmel": ["Sidney Kimmel Medical College", "Thomas Jefferson University"],
    "miami-miller": ["University of Miami Miller School of Medicine", "University of Miami"],
    "wake-forest": ["Wake Forest University School of Medicine", "Wake Forest"],
    "albany": ["Albany Medical College"],
    "drexel": ["Drexel University College of Medicine", "Drexel University"],
    "wayne-state": ["Wayne State University School of Medicine", "Wayne State University"],
    "loyola-stritch": ["Loyola University Chicago Stritch School of Medicine", "Loyola University Chicago"],
    "quinnipiac-netter": ["Frank H. Netter MD School of Medicine", "Quinnipiac University"],
    "tulane": ["Tulane University School of Medicine", "Tulane University"],
    "eastern-virginia": ["Eastern Virginia Medical School", "Old Dominion University"],
    "rush": ["Rush Medical College", "Rush University Medical Center"],
    "rosalind-franklin": ["Chicago Medical School", "Rosalind Franklin University"],
    "new-york-medical-college": ["New York Medical College"],
    "uc-riverside": ["University of California Riverside School of Medicine", "UC Riverside"],
    "cusm": ["California University of Science and Medicine"],
    "umass-chan": ["UMass Chan Medical School", "University of Massachusetts Chan Medical School"],
    "nova-southeastern-md": ["Nova Southeastern University Dr. Kiran C. Patel College of Allopathic Medicine", "Nova Southeastern University"],
    "roseman": ["Roseman University College of Medicine", "Roseman University"],
    "hackensack-meridian": ["Hackensack Meridian School of Medicine", "Hackensack Meridian"],
    "belmont-frist": ["Thomas F. Frist Jr. College of Medicine", "Belmont University"],
    "uicom": ["University of Illinois College of Medicine", "University of Illinois Chicago"],
    "george-washington": ["George Washington University School of Medicine", "George Washington University"],
    "california-northstate": ["California Northstate University College of Medicine", "California Northstate University"],
}

THEME_TERMS = [
    "health disparities",
    "community health",
    "underserved",
    "medical education",
    "clinical",
    "infection",
    "microbiology",
    "women's health",
    "public health",
    "health equity",
]


def request_json(endpoint: str, params: dict[str, str]) -> dict:
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "med-school-app-workspace/1.0"})
    with urllib.request.urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def request_xml(endpoint: str, params: dict[str, str]) -> ET.Element:
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "med-school-app-workspace/1.0"})
    with urllib.request.urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
        return ET.fromstring(response.read())


def build_query(slug: str) -> str:
    affiliations = AFFILIATION_TERMS.get(slug, [])
    affiliation_query = " OR ".join(f'"{term}"[Affiliation]' for term in affiliations)
    theme_query = " OR ".join(f'"{term}"[Title/Abstract]' for term in THEME_TERMS)
    return f"({affiliation_query}) AND ({theme_query}) AND (2021:3000[pdat])"


def search_pubmed(slug: str) -> list[str]:
    query = build_query(slug)
    data = request_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": "6",
            "sort": "relevance",
        },
    )
    return data.get("esearchresult", {}).get("idlist", [])


def text_of(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def article_year(article: ET.Element) -> str:
    for path in [
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubMedPubDate/Year",
    ]:
        value = text_of(article.find(path))
        if value:
            return value
    return ""


def article_doi(article: ET.Element) -> str:
    for article_id in article.findall(".//ArticleId"):
        if article_id.attrib.get("IdType") == "doi":
            return text_of(article_id)
    return ""


def article_authors(article: ET.Element) -> str:
    names = []
    for author in article.findall(".//Author")[:3]:
        last = text_of(author.find("LastName"))
        initials = text_of(author.find("Initials"))
        if last:
            names.append(f"{last} {initials}".strip())
    if len(names) == 3:
        names.append("et al.")
    return ", ".join(names)


def make_synopsis(title: str, abstract: str) -> str:
    if abstract:
        first_sentence = abstract.split(". ", 1)[0].strip()
        if len(first_sentence) > 280:
            first_sentence = first_sentence[:277].rsplit(" ", 1)[0] + "..."
        return f"This is useful for school-fit writing because it shows active work in an area adjacent to your service, public-health, clinical, or research narrative. Paper focus: {first_sentence}."
    return f"This is useful for school-fit writing because it shows recent scholarship connected to your research, clinical, service, or public-health narrative. Paper focus: {title}."


def fetch_articles(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    root = request_xml(
        "efetch.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        },
    )
    papers = []
    seen_titles = set()
    for article in root.findall(".//PubmedArticle"):
        pmid = text_of(article.find(".//PMID"))
        title = text_of(article.find(".//ArticleTitle"))
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        journal = text_of(article.find(".//Journal/Title"))
        abstract = text_of(article.find(".//Abstract"))
        doi = article_doi(article)
        papers.append(
            {
                "pmid": pmid,
                "title": title,
                "authors": article_authors(article),
                "journal": journal,
                "year": article_year(article),
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "synopsis": make_synopsis(title, abstract),
            }
        )
    return papers[:3]


def main() -> None:
    schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
    output: dict[str, list[dict]] = {}
    for school in schools:
        slug = school["slug"]
        try:
            pmids = search_pubmed(slug)
            time.sleep(0.34)
            output[slug] = fetch_articles(pmids)
            time.sleep(0.34)
            print(f"{slug}: {len(output[slug])} paper(s)")
        except Exception as exc:  # Keep partial output useful if one query fails.
            output[slug] = []
            print(f"{slug}: failed: {exc}")
    OUTPUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
