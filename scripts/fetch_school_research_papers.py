#!/usr/bin/env python3
"""Fetch PubMed papers that are worth citing in school-fit research notes.

The output is intentionally selective: at most one paper per school, chosen only
when it is major, microbiology/infectious-disease adjacent, or tightly connected
to the applicant's experience themes such as underserved care, hospice/palliative
care, or women's health. If the best match is weak, the school is left blank.
"""

from __future__ import annotations

import json
import re
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
    "antimicrobial",
    "antibiotic",
    "bacteremia",
    "health disparities",
    "health equity",
    "hospice",
    "infection",
    "infectious disease",
    "maternal",
    "microbiology",
    "microbiome",
    "palliative",
    "pregnancy",
    "sepsis",
    "underserved",
    "vaccine",
    "virus",
    "women's health",
]

MAJOR_JOURNALS = {
    "The New England journal of medicine": 80,
    "Lancet (London, England)": 75,
    "JAMA": 72,
    "Nature": 72,
    "Science": 72,
    "Cell": 70,
    "Nature medicine": 68,
    "The Lancet. Infectious diseases": 68,
    "The Lancet. Global health": 66,
    "JAMA internal medicine": 64,
    "JAMA network open": 58,
    "Clinical infectious diseases : an official publication of the Infectious Diseases Society of America": 56,
    "Antimicrobial agents and chemotherapy": 52,
    "American journal of obstetrics and gynecology": 50,
    "Obstetrics and gynecology": 48,
    "Pediatrics": 46,
    "Annual review of public health": 46,
    "Nature reviews. Microbiology": 60,
    "Nature reviews. Disease primers": 52,
    "Nature reviews. Cardiology": 44,
}

RELEVANCE_TERMS = {
    "microbio / infectious disease": [
        "antimicrobial",
        "antibiotic",
        "bacteria",
        "bacterial",
        "bacteremia",
        "candida",
        "candidiasis",
        "cmv",
        "coccidioidomycosis",
        "helicobacter",
        "infectious disease",
        "infectious diseases",
        "infectious",
        "microbiology",
        "microbiome",
        "mrsa",
        "pathogen",
        "phage",
        "pseudomonas",
        "sepsis",
        "staphylococcus",
        "syphilis",
        "toxoplasmosis",
        "urinary tract infection",
        "urinary tract infections",
        "vaccine",
        "virus",
    ],
    "women's health": [
        "breast cancer",
        "chorioamnionitis",
        "gynecolog",
        "maternal",
        "menopaus",
        "obstetric",
        "postpartum",
        "preeclampsia",
        "pregnancy",
        "pregnant",
        "vaginal",
        "women",
        "women's health",
    ],
    "underserved / health equity": [
        "bias",
        "disparit",
        "equity",
        "food insecurity",
        "global burden",
        "health care access",
        "health inequ",
        "minority",
        "public health",
        "social determinant",
        "structural",
        "underserved",
    ],
    "hospice / palliative care": [
        "advance care",
        "end-of-life",
        "hospice",
        "palliat",
        "serious illness",
    ],
}

IMPORTANT_DESIGNS = [
    "clinical trial",
    "consensus",
    "guideline",
    "meta-analysis",
    "multicentre",
    "multicenter",
    "randomized",
    "systematic analysis",
    "systematic review",
]

LOW_SIGNAL_TERMS = [
    "alopecia",
    "beeswax",
    "cosmetic",
    "dermatology",
    "eyebrow",
    "eyelash",
    "facial",
    "hair growth",
    "hair loss",
    "rejuvenation",
    "skincare",
]

MIN_SCORE = 82
REJECTION_TYPES = ["Editorial", "Letter", "News", "Comment"]

MANUAL_SELECTIONS: dict[str, list[dict[str, str | int]]] = {
    "temple": [
        {
            "pmid": "38085312",
            "title": "Metformin Plus Insulin for Preexisting Diabetes or Gestational Diabetes in Early Pregnancy: The MOMPOD Randomized Clinical Trial.",
            "authors": "",
            "journal": "JAMA",
            "year": "2023",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38085312/",
            "synopsis": "Selected because it is a major randomized clinical trial in pregnancy and maternal health, which is more useful for your application themes than a generic high-impact paper outside your story.",
            "score": 999,
            "selection_reason": "manual selection; women's health; high-impact venue: JAMA; randomized clinical trial",
        }
    ],
    "virginia-tech-carilion": [
        {
            "pmid": "40802264",
            "title": "Dalbavancin for Treatment of Staphylococcus aureus Bacteremia: The DOTS Randomized Clinical Trial.",
            "authors": "",
            "journal": "JAMA",
            "year": "2025",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/40802264/",
            "synopsis": "Selected because it is a major randomized clinical trial in Staphylococcus aureus bacteremia, making it directly useful for microbiology and infectious-disease framing.",
            "score": 999,
            "selection_reason": "manual selection; microbio / infectious disease; high-impact venue: JAMA; randomized clinical trial",
        }
    ],
    "wake-forest": [
        {
            "pmid": "40802264",
            "title": "Dalbavancin for Treatment of Staphylococcus aureus Bacteremia: The DOTS Randomized Clinical Trial.",
            "authors": "",
            "journal": "JAMA",
            "year": "2025",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/40802264/",
            "synopsis": "Selected because it is a major randomized clinical trial in Staphylococcus aureus bacteremia, making it directly useful for microbiology and infectious-disease framing.",
            "score": 999,
            "selection_reason": "manual selection; microbio / infectious disease; high-impact venue: JAMA; randomized clinical trial",
        }
    ],
    "rosalind-franklin": [
        {
            "pmid": "34350458",
            "title": "Clinical Practice Guideline by the Pediatric Infectious Diseases Society and the Infectious Diseases Society of America: 2021 Guideline on Diagnosis and Management of Acute Hematogenous Osteomyelitis in Pediatrics.",
            "authors": "",
            "journal": "Journal of the Pediatric Infectious Diseases Society",
            "year": "2021",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/34350458/",
            "synopsis": "Selected because it is an infectious-disease clinical practice guideline, which is substantially stronger for your microbiology narrative than a generic clinical AI paper.",
            "score": 999,
            "selection_reason": "manual selection; microbio / infectious disease; clinical guideline",
        }
    ],
    "new-york-medical-college": [
        {
            "pmid": "38353950",
            "title": "Digital Health Interventions for Hypertension Management in US Populations Experiencing Health Disparities: A Systematic Review and Meta-Analysis.",
            "authors": "",
            "journal": "JAMA Network Open",
            "year": "2024",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38353950/",
            "synopsis": "Selected because it directly connects to care for populations experiencing health disparities and is more usable for your service narrative than a narrow obstetrics review.",
            "score": 999,
            "selection_reason": "manual selection; underserved / health equity; high-impact venue: JAMA Network Open; meta-analysis",
        }
    ],
    "umass-chan": [
        {
            "pmid": "36803604",
            "title": "The choroid plexus links innate immunity to CSF dysregulation in hydrocephalus.",
            "authors": "",
            "journal": "Cell",
            "year": "2023",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/36803604/",
            "synopsis": "Selected because it is a major Cell paper connecting innate immunity to disease mechanism, which is a stronger science contribution than a generic digital-health intervention.",
            "score": 999,
            "selection_reason": "manual selection; immunology / disease mechanism; high-impact venue: Cell",
        }
    ],
    "uicom": [
        {
            "pmid": "39701120",
            "title": "Effectiveness of ceftazidime-avibactam versus ceftolozane-tazobactam for multidrug-resistant Pseudomonas aeruginosa infections in the USA (CACTUS): a multicentre, retrospective, observational study.",
            "authors": "",
            "journal": "The Lancet Infectious Diseases",
            "year": "2025",
            "doi": "",
            "url": "https://pubmed.ncbi.nlm.nih.gov/39701120/",
            "synopsis": "Selected because it is directly microbiology/infectious-disease relevant and focuses on multidrug-resistant Pseudomonas infections in a major infectious-disease journal.",
            "score": 999,
            "selection_reason": "manual selection; microbio / infectious disease; high-impact venue: The Lancet Infectious Diseases",
        }
    ],
    "albany": [],
    "california-northstate": [],
}


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
    journal_query = " OR ".join(f'"{journal}"[Journal]' for journal in MAJOR_JOURNALS)
    return f"({affiliation_query}) AND (({theme_query}) OR ({journal_query})) AND (2018:3000[pdat])"


def search_pubmed(slug: str) -> list[str]:
    data = request_json(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": build_query(slug),
            "retmode": "json",
            "retmax": "80",
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


def article_types(article: ET.Element) -> list[str]:
    return [text_of(article_type) for article_type in article.findall(".//PublicationType")]


def term_matches(text: str, term: str) -> bool:
    escaped = re.escape(term).replace(r"\ ", r"\W+")
    if term in {"disparit", "gynecolog", "menopaus", "obstetric", "palliat"}:
        pattern = rf"\b{escaped}\w*"
    else:
        pattern = rf"\b{escaped}\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def theme_hits(text: str) -> list[str]:
    return [
        theme
        for theme, terms in RELEVANCE_TERMS.items()
        if any(term_matches(text, term) for term in terms)
    ]


def score_article(title: str, abstract: str, journal: str, year: str, publication_types: list[str]) -> tuple[int, list[str]]:
    text = f"{title} {abstract}".lower()
    score = 0
    reasons: list[str] = []

    matched_themes = theme_hits(text)
    for theme in matched_themes:
        score += 55
        reasons.append(theme)

    if journal in MAJOR_JOURNALS:
        score += MAJOR_JOURNALS[journal]
        reasons.append(f"high-impact venue: {journal}")

    design_text = f"{title} {' '.join(publication_types)}".lower()
    for design in IMPORTANT_DESIGNS:
        if design in design_text:
            score += 20
            reasons.append(design)
            break

    if any(article_type in REJECTION_TYPES for article_type in publication_types):
        score -= 65
        reasons.append("deprioritized commentary/editorial")

    try:
        year_int = int(year)
    except ValueError:
        year_int = 0
    if year_int >= 2023:
        score += 8
    elif year_int and year_int < 2020:
        score -= 10

    if "review" in design_text and not any(
        reason.startswith("high-impact venue") or reason in {"guideline", "consensus"}
        for reason in reasons
    ):
        score -= 12

    if any(term_matches(text, term) for term in LOW_SIGNAL_TERMS):
        score -= 90
        reasons.append("excluded low-signal/cosmetic topic")

    if not matched_themes and not (
        journal in MAJOR_JOURNALS
        and any(design in design_text for design in IMPORTANT_DESIGNS)
    ):
        score -= 100
        reasons.append("no strong applicant-theme match")

    return score, reasons


def make_synopsis(title: str, abstract: str, reasons: list[str]) -> str:
    good_reasons = [reason for reason in reasons if reason != "excluded low-signal/cosmetic topic"]
    reason_text = ", ".join(good_reasons)
    if abstract:
        first_sentence = abstract.split(". ", 1)[0].strip()
        if len(first_sentence) > 250:
            first_sentence = first_sentence[:247].rsplit(" ", 1)[0] + "..."
        return f"Selected because it is a stronger fit for your application themes ({reason_text}). Paper focus: {first_sentence}."
    return f"Selected because it is a stronger fit for your application themes ({reason_text}). Paper focus: {title}."


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
    candidates = []
    seen_titles = set()
    for article in root.findall(".//PubmedArticle"):
        pmid = text_of(article.find(".//PMID"))
        title = text_of(article.find(".//ArticleTitle"))
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        journal = text_of(article.find(".//Journal/Title"))
        abstract = text_of(article.find(".//Abstract"))
        year = article_year(article)
        types = article_types(article)
        score, reasons = score_article(title, abstract, journal, year, types)
        if score < MIN_SCORE:
            continue
        doi = article_doi(article)
        candidates.append(
            {
                "pmid": pmid,
                "title": title,
                "authors": article_authors(article),
                "journal": journal,
                "year": year,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "synopsis": make_synopsis(title, abstract, reasons),
                "score": score,
                "selection_reason": "; ".join(reasons),
            }
        )
    candidates.sort(key=lambda paper: (paper["score"], paper.get("year", "")), reverse=True)
    return candidates[:1]


def main() -> None:
    schools = json.loads(SCHOOLS_JSON.read_text(encoding="utf-8"))
    output: dict[str, list[dict]] = {}
    for school in schools:
        slug = school["slug"]
        if slug in MANUAL_SELECTIONS:
            output[slug] = MANUAL_SELECTIONS[slug]
            title = output[slug][0]["title"] if output[slug] else "no strong paper selected"
            print(f"{slug}: {title}")
            continue
        try:
            pmids = search_pubmed(slug)
            time.sleep(0.34)
            output[slug] = fetch_articles(pmids)
            time.sleep(0.34)
            title = output[slug][0]["title"] if output[slug] else "no strong paper selected"
            print(f"{slug}: {title}")
        except Exception as exc:  # Keep partial output useful if one query fails.
            output[slug] = []
            print(f"{slug}: failed: {exc}")
    OUTPUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
