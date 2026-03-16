"""Static reference registry for standard medical research guidelines and textbooks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaticReference:
    """An immutable static reference entry."""

    key: str
    authors: str
    title: str
    source: str
    year: int
    url: str
    keywords: tuple[str, ...]


REFERENCE_REGISTRY: tuple[StaticReference, ...] = (
    # --- Reporting Guidelines ---
    StaticReference(
        key="consort",
        authors="Schulz KF, Altman DG, Moher D",
        title="CONSORT 2010 Statement: updated guidelines for reporting parallel group randomised trials",
        source="BMJ",
        year=2010,
        url="https://www.equator-network.org/reporting-guidelines/consort/",
        keywords=("consort", "randomised trial", "randomized trial", "rct reporting"),
    ),
    StaticReference(
        key="strobe",
        authors="von Elm E, Altman DG, Egger M, et al.",
        title="The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) Statement",
        source="Ann Intern Med",
        year=2007,
        url="https://www.equator-network.org/reporting-guidelines/strobe/",
        keywords=("strobe", "observational study reporting"),
    ),
    StaticReference(
        key="prisma",
        authors="Page MJ, McKenzie JE, Bossuyt PM, et al.",
        title="The PRISMA 2020 statement: an updated guideline for reporting systematic reviews",
        source="BMJ",
        year=2021,
        url="https://www.equator-network.org/reporting-guidelines/prisma/",
        keywords=("prisma", "systematic review", "meta-analysis reporting"),
    ),
    StaticReference(
        key="spirit",
        authors="Chan AW, Tetzlaff JM, Altman DG, et al.",
        title="SPIRIT 2013 Statement: Defining Standard Protocol Items for Clinical Trials",
        source="Ann Intern Med",
        year=2013,
        url="https://www.equator-network.org/reporting-guidelines/spirit-2013-statement-defining-standard-protocol-items-for-clinical-trials/",
        keywords=("spirit", "clinical trial protocol"),
    ),
    StaticReference(
        key="care",
        authors="Gagnier JJ, Kienle G, Altman DG, et al.",
        title="The CARE Guidelines: Consensus-based Clinical Case Reporting Guideline Development",
        source="BMJ Case Rep",
        year=2013,
        url="https://www.equator-network.org/reporting-guidelines/care/",
        keywords=("care guideline", "case report"),
    ),
    StaticReference(
        key="tripod",
        authors="Collins GS, Reitsma JB, Altman DG, Moons KGM",
        title="Transparent Reporting of a multivariable prediction model for Individual Prognosis or Diagnosis (TRIPOD)",
        source="Ann Intern Med",
        year=2015,
        url="https://www.equator-network.org/reporting-guidelines/tripod-statement/",
        keywords=("tripod", "prediction model", "prognostic model"),
    ),
    StaticReference(
        key="stard",
        authors="Bossuyt PM, Reitsma JB, Bruns DE, et al.",
        title="STARD 2015: An Updated List of Essential Items for Reporting Diagnostic Accuracy Studies",
        source="BMJ",
        year=2015,
        url="https://www.equator-network.org/reporting-guidelines/stard/",
        keywords=("stard", "diagnostic accuracy"),
    ),
    # --- Frameworks & Ethics ---
    StaticReference(
        key="equator",
        authors="EQUATOR Network",
        title="Enhancing the QUAlity and Transparency Of health Research",
        source="EQUATOR Network",
        year=2008,
        url="https://www.equator-network.org/",
        keywords=("equator", "reporting guideline", "equator network"),
    ),
    StaticReference(
        key="grade",
        authors="Guyatt GH, Oxman AD, Vist GE, et al.",
        title="GRADE: an emerging consensus on rating quality of evidence and strength of recommendations",
        source="BMJ",
        year=2008,
        url="https://www.bmj.com/content/336/7650/924",
        keywords=("grade", "evidence quality", "strength of recommendation"),
    ),
    StaticReference(
        key="helsinki",
        authors="World Medical Association",
        title="Declaration of Helsinki: Ethical Principles for Medical Research Involving Human Subjects",
        source="JAMA",
        year=2013,
        url="https://www.wma.net/policies-post/wma-declaration-of-helsinki/",
        keywords=("helsinki", "declaration of helsinki", "research ethics"),
    ),
    StaticReference(
        key="finer",
        authors="Hulley SB, Cummings SR, Browner WS, et al.",
        title="Designing Clinical Research (FINER criteria)",
        source="Lippincott Williams & Wilkins",
        year=2013,
        url="https://www.lww.com/",
        keywords=("finer", "feasible novel ethical relevant"),
    ),
    # --- Textbooks ---
    StaticReference(
        key="chow_sample_size",
        authors="Chow SC, Shao J, Wang H, Lokhnygina Y",
        title="Sample Size Calculations in Clinical Research",
        source="Chapman and Hall/CRC",
        year=2018,
        url="https://www.routledge.com/Sample-Size-Calculations-in-Clinical-Research/Chow-Shao-Wang-Lokhnygina/p/book/9781138740983",
        keywords=("chow", "shao", "wang", "sample size calculation"),
    ),
    StaticReference(
        key="machin_sample_size",
        authors="Machin D, Campbell MJ, Tan SB, Tan SH",
        title="Sample Sizes for Clinical, Laboratory and Epidemiology Studies",
        source="Wiley-Blackwell",
        year=2018,
        url="https://www.wiley.com/",
        keywords=("machin", "sample size"),
    ),
    StaticReference(
        key="cohen_power",
        authors="Cohen J",
        title="Statistical Power Analysis for the Behavioral Sciences",
        source="Routledge",
        year=1988,
        url="https://www.routledge.com/Statistical-Power-Analysis-for-the-Behavioral-Sciences/Cohen/p/book/9780805802832",
        keywords=("cohen", "power analysis", "effect size"),
    ),
    # --- Gap Taxonomy ---
    StaticReference(
        key="robinson_gaps",
        authors="Robinson KA, Saldanha IJ, McKoy NA",
        title="Development of a framework to identify research gaps from systematic reviews",
        source="J Clin Epidemiol",
        year=2011,
        url="https://pubmed.ncbi.nlm.nih.gov/21130354/",
        keywords=("robinson", "research gap", "gap framework", "gap taxonomy"),
    ),
    StaticReference(
        key="mueller_bloch",
        authors="Mueller-Bloch C, Kranz J",
        title="A Framework for Rigorously Identifying Research Gaps in Qualitative Literature Reviews",
        source="ICIS 2015 Proceedings",
        year=2015,
        url="https://aisel.aisnet.org/icis2015/proceedings/ResearchMethods/7/",
        keywords=("mueller-bloch", "kranz", "research gap identification"),
    ),
    # --- Standards ---
    StaticReference(
        key="ich_e9",
        authors="ICH Expert Working Group",
        title="ICH E9: Statistical Principles for Clinical Trials",
        source="International Council for Harmonisation",
        year=1998,
        url="https://www.ich.org/page/quality-guidelines",
        keywords=("ich e9", "ich-e9", "statistical principles clinical trial"),
    ),
    StaticReference(
        key="ich_e6",
        authors="ICH Expert Working Group",
        title="ICH E6(R2): Guideline for Good Clinical Practice",
        source="International Council for Harmonisation",
        year=2016,
        url="https://www.ich.org/page/efficacy-guidelines",
        keywords=("ich e6", "good clinical practice", "gcp"),
    ),
)


def find_matching_references(text: str) -> list[StaticReference]:
    """Return static references whose keywords appear in the given text.

    Matching is case-insensitive. Each reference is returned at most once.
    """
    lower_text = text.lower()
    return [
        ref
        for ref in REFERENCE_REGISTRY
        if any(kw in lower_text for kw in ref.keywords)
    ]
