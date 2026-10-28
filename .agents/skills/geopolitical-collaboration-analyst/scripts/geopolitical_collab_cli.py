#!/usr/bin/env python3
"""
CLI Helper: Geopolitical Collaboration Analyst
Analyzes international co-authorship networks, bilateral Salton similarity,
regional geopolitical groupings (Iberoamerica, GlobalSouth, OECD, BRICS, EU),
scientific leadership (first & corresponding author sovereignty ratios),
and generates interactive standalone HTML visualization dashboards.
"""

import sys
import os
import json
import csv
import math
import re
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Set, Tuple

# ==============================================================================
# 1. CANONICAL ISO-3166-1 DICTIONARIES (Alpha-2 to Alpha-3 and Name Mapping)
# ==============================================================================

ISO2_TO_ISO3: Dict[str, str] = {
    "AF": "AFG", "AX": "ALA", "AL": "ALB", "DZ": "DZA", "AS": "ASM", "AD": "AND", "AO": "AGO", "AI": "AIA",
    "AQ": "ATA", "AG": "ATG", "AR": "ARG", "AM": "ARM", "AW": "ABW", "AU": "AUS", "AT": "AUT", "AZ": "AZE",
    "BS": "BHS", "BH": "BHR", "BD": "BGD", "BB": "BRB", "BY": "BLR", "BE": "BEL", "BZ": "BLZ", "BJ": "BEN",
    "BM": "BMU", "BT": "BTN", "BO": "BOL", "BQ": "BES", "BA": "BIH", "BW": "BWA", "BV": "BVT", "BR": "BRA",
    "IO": "IOT", "BN": "BRN", "BG": "BGR", "BF": "BFA", "BI": "BDI", "CV": "CPV", "KH": "KHM", "CM": "CMR",
    "CA": "CAN", "KY": "CYM", "CF": "CAF", "TD": "TCD", "CL": "CHL", "CN": "CHN", "CX": "CXR", "CC": "CCK",
    "CO": "COL", "KM": "COM", "CG": "COG", "CD": "COD", "CK": "COK", "CR": "CRI", "CI": "CIV", "HR": "HRV",
    "CU": "CUB", "CW": "CUW", "CY": "CYP", "CZ": "CZE", "DK": "DNK", "DJ": "DJI", "DM": "DMA", "DO": "DOM",
    "EC": "ECU", "EG": "EGY", "SV": "SLV", "GQ": "GNQ", "ER": "ERI", "EE": "EST", "SZ": "SWZ", "ET": "ETH",
    "FK": "FLK", "FO": "FRO", "FJ": "FJI", "FI": "FIN", "FR": "FRA", "GF": "GUF", "PF": "PYF", "TF": "ATF",
    "GA": "GAB", "GM": "GMB", "GE": "GEO", "DE": "DEU", "GH": "GHA", "GI": "GIB", "GR": "GRC", "GL": "GRL",
    "GD": "GRD", "GP": "GLP", "GU": "GUM", "GT": "GTM", "GG": "GGY", "GN": "GIN", "GW": "GNB", "GY": "GUY",
    "HT": "HTI", "HM": "HMD", "VA": "VAT", "HN": "HND", "HK": "HKG", "HU": "HUN", "IS": "ISL", "IN": "IND",
    "ID": "IDN", "IR": "IRN", "IQ": "IRQ", "IE": "IRL", "IM": "IMN", "IL": "ISR", "IT": "ITA", "JM": "JAM",
    "JP": "JPN", "JE": "JEY", "JO": "JOR", "KZ": "KAZ", "KE": "KEN", "KI": "KIR", "KP": "PRK", "KR": "KOR",
    "KW": "KWT", "KG": "KGZ", "LA": "LAO", "LV": "LVA", "LB": "LBN", "LS": "LSO", "LR": "LBR", "LY": "LBY",
    "LI": "LIE", "LT": "LTU", "LU": "LUX", "MO": "MAC", "MG": "MDG", "MW": "MWI", "MY": "MYS", "MV": "MDV",
    "ML": "MLI", "MT": "MLT", "MH": "MHL", "MQ": "MTQ", "MR": "MRT", "MU": "MUS", "YT": "MYT", "MX": "MEX",
    "FM": "FSM", "MD": "MDA", "MC": "MCO", "MN": "MNG", "ME": "MNE", "MS": "MSR", "MA": "MAR", "MZ": "MOZ",
    "MM": "MMR", "NA": "NAM", "NR": "NRU", "NP": "NPL", "NL": "NLD", "NC": "NCL", "NZ": "NZL", "NI": "NIC",
    "NE": "NER", "NG": "NGA", "NU": "NIU", "NF": "NFK", "MK": "MKD", "MP": "MNP", "NO": "NOR", "OM": "OMN",
    "PK": "PAK", "PW": "PLW", "PS": "PSE", "PA": "PAN", "PG": "PNG", "PY": "PRY", "PE": "PER", "PH": "PHL",
    "PN": "PCN", "PL": "POL", "PT": "PRT", "PR": "PRI", "QA": "QAT", "RE": "REU", "RO": "ROU", "RU": "RUS",
    "RW": "RWA", "BL": "BLM", "SH": "SHN", "KN": "KNA", "LC": "LCA", "MF": "MAF", "PM": "SPM", "VC": "VCT",
    "WS": "WSM", "SM": "SMR", "ST": "STP", "SA": "SAU", "SN": "SEN", "RS": "SRB", "SC": "SYC", "SL": "SLE",
    "SG": "SGP", "SX": "SXM", "SK": "SVK", "SI": "SVN", "SB": "SLB", "SO": "SOM", "ZA": "ZAF", "GS": "SGS",
    "SS": "SSD", "ES": "ESP", "LK": "LKA", "SD": "SDN", "SR": "SUR", "SJ": "SJM", "SE": "SWE", "CH": "CHE",
    "SY": "SYR", "TW": "TWN", "TJ": "TJK", "TZ": "TZA", "TH": "THA", "TL": "TLS", "TG": "TGO", "TK": "TKL",
    "TO": "TON", "TT": "TTO", "TN": "TUN", "TR": "TUR", "TM": "TKM", "TC": "TCA", "TV": "TUV", "UG": "UGA",
    "UA": "UKR", "AE": "ARE", "GB": "GBR", "US": "USA", "UM": "UMI", "UY": "URY", "UZ": "UZB", "VU": "VUT",
    "VE": "VEN", "VN": "VNM", "VG": "VGB", "VI": "VIR", "WF": "WLF", "EH": "ESH", "YE": "YEM", "ZM": "ZMB",
    "ZW": "ZWE"
}

ISO3_TO_NAME: Dict[str, str] = {
    "MEX": "México", "USA": "Estados Unidos", "ESP": "España", "FRA": "Francia", "BRA": "Brasil",
    "GBR": "Reino Unido", "DEU": "Alemania", "CAN": "Canadá", "CHL": "Chile", "COL": "Colombia",
    "ARG": "Argentina", "CHN": "China", "JPN": "Japón", "ITA": "Italia", "PRT": "Portugal",
    "IND": "India", "ZAF": "Sudáfrica", "KOR": "Corea del Sur", "NLD": "Países Bajos",
    "CHE": "Suiza", "AUS": "Australia", "AUT": "Austria", "BEL": "Bélgica", "SWE": "Suecia",
    "NOR": "Noruega", "DNK": "Dinamarca", "FIN": "Finlandia", "POL": "Polonia", "CZE": "República Checa",
    "HUN": "Hungría", "GRC": "Grecia", "TUR": "Turquía", "ISR": "Israel", "RUS": "Rusia",
    "EGY": "Egipto", "PER": "Perú", "CUB": "Cuba", "ECU": "Ecuador", "URY": "Uruguay",
    "VEN": "Venezuela", "CRI": "Costa Rica", "PAN": "Panamá", "BOL": "Bolivia", "PRY": "Paraguay",
    "GTM": "Guatemala", "DOM": "República Dominicana", "HND": "Honduras", "SLV": "El Salvador",
    "NIC": "Nicaragua", "TWN": "Taiwán", "SGP": "Singapur", "MYS": "Malasia", "THA": "Tailandia",
    "VNM": "Vietnam", "IDN": "Indonesia", "PHL": "Filipinas", "PAK": "Pakistán", "IRN": "Irán",
    "SAU": "Arabia Saudita", "ARE": "Emiratos Árabes Unidos", "NZL": "Nueva Zelanda", "IRL": "Irlanda",
    "UKR": "Ucrania", "KEN": "Kenia", "NGA": "Nigeria", "MAR": "Marruecos", "DZA": "Argelia"
}

# Multi-lingual & Bibliographic name alias mappings
COUNTRY_NAME_VARIANTS: Dict[str, str] = {
    # USA
    "united states": "USA", "usa": "USA", "united states of america": "USA", "u s a": "USA", "us": "USA",
    # UK & Home Nations
    "united kingdom": "GBR", "uk": "GBR", "u k": "GBR", "great britain": "GBR", "britain": "GBR",
    "england": "GBR", "scotland": "GBR", "wales": "GBR", "northern ireland": "GBR",
    # China
    "china": "CHN", "peoples r china": "CHN", "people's republic of china": "CHN", "pr china": "CHN",
    "p r china": "CHN", "mainland china": "CHN", "peoples republic of china": "CHN",
    # South Korea
    "south korea": "KOR", "korea": "KOR", "republic of korea": "KOR", "rep korea": "KOR", "r korea": "KOR",
    # North Korea
    "north korea": "PRK", "democratic people's republic of korea": "PRK", "dpr korea": "PRK",
    # Germany
    "germany": "DEU", "alemania": "DEU", "deutschland": "DEU", "fed rep germany": "DEU",
    "federal republic of germany": "DEU", "german dem rep": "DEU",
    # Spain
    "spain": "ESP", "españa": "ESP", "espana": "ESP",
    # France
    "france": "FRA", "francia": "FRA",
    # Brazil
    "brazil": "BRA", "brasil": "BRA",
    # Mexico
    "mexico": "MEX", "méxico": "MEX",
    # Italy
    "italy": "ITA", "italia": "ITA",
    # Canada
    "canada": "CAN", "canadá": "CAN",
    # Japan
    "japan": "JPN", "japón": "JPN", "japon": "JPN",
    # Russia
    "russia": "RUS", "russian federation": "RUS", "rusia": "RUS", "ussr": "RUS",
    # Netherlands
    "netherlands": "NLD", "the netherlands": "NLD", "holland": "NLD", "países bajos": "NLD", "paises bajos": "NLD",
    # Switzerland
    "switzerland": "CHE", "suiza": "CHE", "schweiz": "CHE", "suisse": "CHE",
    # Australia & Austria
    "australia": "AUS", "austria": "AUT",
    # Belgium
    "belgium": "BEL", "bélgica": "BEL", "belgica": "BEL",
    # Sweden, Norway, Denmark, Finland, Poland
    "sweden": "SWE", "suecia": "SWE", "norway": "NOR", "noruega": "NOR",
    "denmark": "DNK", "dinamarca": "DNK", "finland": "FIN", "finlandia": "FIN",
    "poland": "POL", "polonia": "POL", "portugal": "PRT",
    # Czech, Slovakia, Hungary, Greece
    "czech republic": "CZE", "czechia": "CZE", "república checa": "CZE", "republica checa": "CZE",
    "slovakia": "SVK", "eslovaquia": "SVK", "hungary": "HUN", "hungría": "HUN", "hungria": "HUN",
    "greece": "GRC", "grecia": "GRC", "turkey": "TUR", "turquía": "TUR", "turquia": "TUR", "türkiye": "TUR",
    "israel": "ISR", "india": "IND", "south africa": "ZAF", "sudáfrica": "ZAF", "sudafrica": "ZAF",
    "egypt": "EGY", "egipto": "EGY", "chile": "CHL", "colombia": "COL", "argentina": "ARG",
    "peru": "PER", "perú": "PER", "cuba": "CUB", "ecuador": "ECU", "uruguay": "URY",
    "venezuela": "VEN", "costa rica": "CRI", "panama": "PAN", "panamá": "PAN",
    "bolivia": "BOL", "paraguay": "PRY", "taiwan": "TWN", "republic of china": "TWN",
    "singapore": "SGP", "singapur": "SGP", "malaysia": "MYS", "malasia": "MYS",
    "thailand": "THA", "tailandia": "THA", "vietnam": "VNM", "viet nam": "VNM",
    "indonesia": "IDN", "philippines": "PHL", "filipinas": "PHL", "pakistan": "PAK", "pakistán": "PAK",
    "iran": "IRN", "irán": "IRN", "islamic republic of iran": "IRN",
    "saudi arabia": "SAU", "arabia saudita": "SAU", "united arab emirates": "ARE", "uae": "ARE",
    "emiratos árabes unidos": "ARE", "new zealand": "NZL", "nueva zelanda": "NZL",
    "ireland": "IRL", "irlanda": "IRL", "ukraine": "UKR", "ucrania": "UKR",
    "morocco": "MAR", "marruecos": "MAR", "nigeria": "NGA", "kenya": "KEN", "kenia": "KEN",
    "algeria": "DZA", "argelia": "DZA", "guatemala": "GTM", "dominican republic": "DOM",
    "república dominicana": "DOM", "republica dominicana": "DOM", "honduras": "HND",
    "el salvador": "SLV", "nicaragua": "NIC", "andorra": "AND"
}

# ==============================================================================
# 2. REGIONAL GEOPOLITICAL GROUPINGS
# ==============================================================================

REGIONAL_GROUPINGS: Dict[str, Set[str]] = {
    "iberoamerica": {
        "ARG", "BOL", "BRA", "CHL", "COL", "CRI", "CUB", "DOM", "ECU", "ESP",
        "GTM", "HND", "MEX", "NIC", "PAN", "PER", "PRT", "PRY", "SLV", "URY",
        "VEN", "AND"
    },
    "globalsouth": {
        "AFG", "DZA", "AGO", "ARG", "BGD", "BLZ", "BEN", "BTN", "BOL", "BWA",
        "BRA", "BFA", "BDI", "KHM", "CMR", "CPV", "CAF", "TCD", "CHL", "COL",
        "COM", "COG", "COD", "CRI", "CIV", "CUB", "DJI", "DOM", "ECU", "EGY",
        "SLV", "GNQ", "ERI", "SWZ", "ETH", "FJI", "GAB", "GMB", "GHA", "GTM",
        "GIN", "GNB", "GUY", "HTI", "HND", "IND", "IDN", "IRN", "IRQ", "JAM",
        "JOR", "KEN", "PRK", "LAO", "LBN", "LSO", "LBR", "LBY", "MDG", "MWI",
        "MYS", "MDV", "MLI", "MRT", "MUS", "MEX", "MNG", "MAR", "MOZ", "MMR",
        "NAM", "NPL", "NIC", "NER", "NGA", "OMN", "PAK", "PAN", "PNG", "PRY",
        "PER", "PHL", "RWA", "WSM", "STP", "SAU", "SEN", "SLE", "SLB", "SOM",
        "ZAF", "LKA", "SDN", "SUR", "SYR", "TJK", "TZA", "THA", "TLS", "TGO",
        "TON", "TTO", "TUN", "TUR", "TKM", "UGA", "ARE", "URY", "UZB", "VUT",
        "VEN", "VNM", "YEM", "ZMB", "ZWE"
    },
    "oecd": {
        "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST",
        "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN",
        "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT",
        "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA"
    },
    "brics": {
        "BRA", "RUS", "IND", "CHN", "ZAF", "EGY", "ETH", "IRN", "ARE", "SAU"
    },
    "european_union": {
        "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
        "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"
    }
}

# ==============================================================================
# 3. TEXT NORMALIZATION & ADDRESS PARSING
# ==============================================================================

def clean_country_text(text: str) -> str:
    """Strips punctuation, braces, quotes and excess whitespace."""
    t = text.strip().lower()
    t = re.sub(r"[.\(\)\[\]\"\'\:\;]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def resolve_country_code(raw: str) -> Optional[str]:
    """
    Resolves raw affiliation string/segment to ISO-3166-1 alpha-3 code.
    NEVER uses blind truncation fallback (e.g. clean[:3]).
    """
    if not raw:
        return None
    raw_clean = clean_country_text(raw)
    if not raw_clean:
        return None

    # 1. Exact match in name variants dictionary
    if raw_clean in COUNTRY_NAME_VARIANTS:
        return COUNTRY_NAME_VARIANTS[raw_clean]

    # 2. Check uppercase ISO-3
    upper_raw = raw.strip().upper().replace(".", "")
    if len(upper_raw) == 3 and upper_raw in ISO2_TO_ISO3.values():
        return upper_raw

    # 3. Check tokens from rightmost end (address ends with country, possibly with zip code)
    # e.g., "Honolulu, HI 96822 USA" -> tokens: ["honolulu", "hi", "96822", "usa"]
    tokens = raw_clean.split()
    for n in (1, 2, 3, 4):
        if len(tokens) >= n:
            tail = " ".join(tokens[-n:])
            if tail in COUNTRY_NAME_VARIANTS:
                return COUNTRY_NAME_VARIANTS[tail]
            tail_upper = tail.upper()
            if len(tail_upper) == 3 and tail_upper in ISO2_TO_ISO3.values():
                return tail_upper

    # 4. Check compound multi-word substring match for unambiguous names
    for name, code in COUNTRY_NAME_VARIANTS.items():
        if len(name) > 4 and name in raw_clean:
            return code

    return None

def split_wos_c1_blocks(c1_str: str) -> List[str]:
    """
    Splits Web of Science C1 string by semicolons or period-bracket (. [) outside of [Author list] brackets.
    """
    blocks = []
    current = []
    in_bracket = False
    chars = list(c1_str)
    n = len(chars)
    i = 0
    while i < n:
        ch = chars[i]
        if ch == '[':
            in_bracket = True
            current.append(ch)
            i += 1
        elif ch == ']':
            in_bracket = False
            current.append(ch)
            i += 1
        elif not in_bracket and ch == ';':
            b = "".join(current).strip()
            if b:
                blocks.append(b)
            current = []
            i += 1
        elif not in_bracket and ch == '.' and i + 1 < n and (chars[i+1] == '[' or (chars[i+1] == ' ' and i + 2 < n and chars[i+2] == '[')):
            # Matches ".[", ". [", or ".; [" outside brackets
            b = "".join(current).strip()
            if b:
                blocks.append(b)
            current = []
            # skip the period and optional spaces
            i += 1
            while i < n and chars[i] in (' ', ';'):
                i += 1
        else:
            current.append(ch)
            i += 1
    tail = "".join(current).strip()
    if tail:
        blocks.append(tail)
    return blocks

def extract_countries_from_wos_address(address_str: str) -> List[str]:
    """Extracts unique ISO3 country codes from a single or multi-affiliation address block."""
    countries = []
    # Strip brackets containing author names
    cleaned = re.sub(r"\[.*?\]", "", address_str)
    aff_blocks = [b.strip() for b in cleaned.split(";") if b.strip()]

    for aff in aff_blocks:
        parts = [p.strip() for p in aff.split(",") if p.strip()]
        found = None
        for part in reversed(parts):
            code = resolve_country_code(part)
            if code:
                found = code
                break
        if found and found not in countries:
            countries.append(found)

    return countries

def extract_record_countries(r: Dict[str, Any]) -> Tuple[List[str], Optional[str], List[str]]:
    """
    Extracts (all_countries, first_author_country, corresponding_countries) from a record.
    Supports Web of Science, Scopus, OpenAlex, and generic tabular formats.
    """
    all_countries: List[str] = []
    first_author_country: Optional[str] = None
    corresponding_countries: List[str] = []

    # 1. OpenAlex format
    if "authorships" in r and isinstance(r["authorships"], list):
        authorships = r["authorships"]
        for idx, auth in enumerate(authorships):
            insts = auth.get("institutions", []) or []
            auth_countries = []
            for inst in insts:
                c2 = (inst.get("country_code") or "").upper().strip()
                if c2 in ISO2_TO_ISO3:
                    c3 = ISO2_TO_ISO3[c2]
                    if c3 not in all_countries:
                        all_countries.append(c3)
                    auth_countries.append(c3)
            if idx == 0 and auth_countries:
                first_author_country = auth_countries[0]
            if auth.get("is_corresponding") and auth_countries:
                for c3 in auth_countries:
                    if c3 not in corresponding_countries:
                        corresponding_countries.append(c3)
        return all_countries, first_author_country, corresponding_countries

    # 2. Web of Science format (C1, RP)
    c1 = r.get("C1") or r.get("c1") or ""
    rp = r.get("RP") or r.get("rp") or ""

    if c1:
        blocks = split_wos_c1_blocks(str(c1))
        for idx, block in enumerate(blocks):
            b_countries = extract_countries_from_wos_address(block)
            for c in b_countries:
                if c not in all_countries:
                    all_countries.append(c)
            if idx == 0 and b_countries and not first_author_country:
                first_author_country = b_countries[0]

    if rp:
        corr_c = extract_countries_from_wos_address(str(rp))
        corresponding_countries.extend(corr_c)

    # 3. Generic Affiliations / Countries fields (Scopus, CSV)
    if not all_countries:
        affils = r.get("affiliations") or r.get("Affiliations") or r.get("Affiliation") or r.get("countries") or ""
        if affils:
            all_countries = extract_countries_from_wos_address(str(affils))
            if all_countries and not first_author_country:
                first_author_country = all_countries[0]

    return all_countries, first_author_country, corresponding_countries

# ==============================================================================
# 4. CORPUS LOADER (TXT, CSV, PARQUET, JSON)
# ==============================================================================

def parse_wos_plaintext(filepath: str) -> List[Dict[str, Any]]:
    """Native parser for Web of Science plain text exports (savedrecs.txt)."""
    records = []
    current_record = {}
    current_tag = None
    current_lines = []

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line_str = line.rstrip("\r\n")
            if not line_str.strip():
                continue
            if line_str.startswith("FN ") or line_str.startswith("VR "):
                continue
            if line_str == "ER":
                if current_tag and current_lines:
                    current_record[current_tag] = " ".join(current_lines).strip()
                    current_tag = None
                    current_lines = []
                if current_record:
                    records.append(current_record)
                    current_record = {}
                continue

            tag_candidate = line_str[:2]
            if len(line_str) >= 2 and tag_candidate.isupper() and (len(line_str) == 2 or line_str[2] == " "):
                if current_tag and current_lines:
                    current_record[current_tag] = " ".join(current_lines).strip()
                current_tag = tag_candidate
                current_lines = [line_str[3:].strip()] if len(line_str) > 3 else []
            elif line_str.startswith("   ") and current_tag:
                stripped = line_str.strip()
                if current_tag == "C1" and stripped.startswith("["):
                    current_lines.append("; " + stripped)
                else:
                    current_lines.append(stripped)

        if current_tag and current_lines:
            current_record[current_tag] = " ".join(current_lines).strip()
        if current_record:
            records.append(current_record)

    return records

def load_corpus(filepath: str) -> List[Dict[str, Any]]:
    """Loads records from TXT (WoS), Parquet, CSV, or JSON."""
    if not os.path.exists(filepath):
        sys.stderr.write(f"Error: Input file does not exist: {filepath}\n")
        sys.exit(1)

    lower = filepath.lower()
    if lower.endswith(".txt"):
        return parse_wos_plaintext(filepath)
    if lower.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(filepath)
        return df.to_dict(orient="records")
    if lower.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            return list(csv.DictReader(f))
    if lower.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", data) if isinstance(data, dict) else data
    return []

# ==============================================================================
# 5. CORE ANALYTICAL COMPUTATIONS
# ==============================================================================

def compute_country_analysis(
    records: List[Dict[str, Any]],
    anchor_country: str = "MEX",
    top_n: int = 25
) -> Dict[str, Any]:
    """
    Computes country co-authorship matrix, Salton cosine similarity,
    regional geopolitical breakdowns, and scientific leadership rates.
    """
    anchor = anchor_country.upper().strip()
    country_doc_counts = Counter()
    collab_pairs = Counter()

    total_intl_papers = 0
    anchor_intl_papers = 0
    first_author_anchor_count = 0
    corr_author_anchor_count = 0

    partner_first_author_counts = Counter()
    partner_corr_author_counts = Counter()

    for r in records:
        countries, first_c, corr_c = extract_record_countries(r)
        if not countries:
            continue

        for c in countries:
            country_doc_counts[c] += 1

        # Check if paper is international
        if len(countries) > 1:
            total_intl_papers += 1
            if anchor in countries:
                anchor_intl_papers += 1
                if first_c == anchor:
                    first_author_anchor_count += 1
                if anchor in corr_c:
                    corr_author_anchor_count += 1

                for c in countries:
                    if c != anchor:
                        if first_c == c:
                            partner_first_author_counts[c] += 1
                        if c in corr_c:
                            partner_corr_author_counts[c] += 1

        # Count bilateral co-authorships
        c_sorted = sorted(countries)
        for i in range(len(c_sorted)):
            for j in range(i + 1, len(c_sorted)):
                collab_pairs[(c_sorted[i], c_sorted[j])] += 1

    anchor_total_papers = country_doc_counts.get(anchor, 0)
    anchor_collabs = []

    for (c1, c2), count in collab_pairs.items():
        partner = None
        if c1 == anchor:
            partner = c2
        elif c2 == anchor:
            partner = c1

        if partner:
            partner_total = country_doc_counts.get(partner, 1)
            denominator = math.sqrt(anchor_total_papers * partner_total) if (anchor_total_papers * partner_total) > 0 else 1.0
            salton = count / denominator
            jaccard = count / (anchor_total_papers + partner_total - count) if (anchor_total_papers + partner_total - count) > 0 else 0.0

            # Determine primary region of partner
            p_region = "Resto del Mundo"
            for r_name, r_set in REGIONAL_GROUPINGS.items():
                if partner in r_set:
                    p_region = r_name.title()
                    break

            anchor_collabs.append({
                "partner_country_iso3": partner,
                "partner_country_name": ISO3_TO_NAME.get(partner, partner),
                "region": p_region,
                "coauthored_papers": count,
                "partner_total_papers": partner_total,
                "salton_cosine_similarity": round(salton, 4),
                "jaccard_similarity": round(jaccard, 4),
                "anchor_first_author_count": anchor_intl_papers - partner_first_author_counts.get(partner, 0),
                "partner_first_author_count": partner_first_author_counts.get(partner, 0)
            })

    anchor_collabs.sort(key=lambda x: (x["coauthored_papers"], x["salton_cosine_similarity"]), reverse=True)

    # Regional Benchmark Breakdown
    regional_breakdown = {}
    total_collab_instances = sum(p["coauthored_papers"] for p in anchor_collabs)

    for reg_key, reg_set in REGIONAL_GROUPINGS.items():
        reg_partners = [p for p in anchor_collabs if p["partner_country_iso3"] in reg_set]
        reg_count = sum(p["coauthored_papers"] for p in reg_partners)
        reg_share = (reg_count / total_collab_instances * 100.0) if total_collab_instances > 0 else 0.0
        regional_breakdown[reg_key] = {
            "region_name": reg_key.title(),
            "collaborations_count": reg_count,
            "percentage_share": round(reg_share, 2),
            "partner_countries_count": len(reg_partners),
            "top_members": [p["partner_country_iso3"] for p in reg_partners[:5]]
        }

    # Scientific Leadership Rates
    first_author_rate = (first_author_anchor_count / anchor_intl_papers * 100.0) if anchor_intl_papers > 0 else 0.0
    corr_author_rate = (corr_author_anchor_count / anchor_intl_papers * 100.0) if anchor_intl_papers > 0 else 0.0

    if first_author_rate >= 50.0:
        sovereignty_status = "Liderazgo Preponderante (Soberanía Científica)"
        sovereignty_badge = "Soberano"
    elif first_author_rate >= 40.0:
        sovereignty_status = "Colaboración Simétrica (Equitativa)"
        sovereignty_badge = "Simétrico"
    elif first_author_rate >= 30.0:
        sovereignty_status = "Participación Secundaria (Dirección Compartida)"
        sovereignty_badge = "Intermedio"
    else:
        sovereignty_status = "Asimetría Epistemológica (Dependencia Norte-Sur)"
        sovereignty_badge = "Asimétrico"

    return {
        "anchor_country_iso3": anchor,
        "anchor_country_name": ISO3_TO_NAME.get(anchor, anchor),
        "total_documents_analyzed": len(records),
        "anchor_total_papers": anchor_total_papers,
        "total_international_papers_corpus": total_intl_papers,
        "anchor_international_papers": anchor_intl_papers,
        "internationalization_rate_pct": round((anchor_intl_papers / anchor_total_papers * 100.0), 2) if anchor_total_papers > 0 else 0.0,
        "total_partner_countries": len(anchor_collabs),
        "total_collaborations_count": total_collab_instances,
        "scientific_leadership": {
            "first_author_led_papers": first_author_anchor_count,
            "first_author_rate_pct": round(first_author_rate, 2),
            "corresponding_author_led_papers": corr_author_anchor_count,
            "corresponding_author_rate_pct": round(corr_author_rate, 2),
            "sovereignty_status": sovereignty_status,
            "sovereignty_badge": sovereignty_badge
        },
        "regional_breakdown": regional_breakdown,
        "top_partners": anchor_collabs[:top_n]
    }

# ==============================================================================
# 6. STANDALONE INTERACTIVE HTML DASHBOARD GENERATOR
# ==============================================================================

def generate_interactive_dashboard_html(data: Dict[str, Any], title: Optional[str] = None) -> str:
    """
    Renders an interactive, standalone HTML dashboard with Plotly charts:
    - Global Choropleth Map of collaboration intensity and Salton affinity.
    - Geopolitical Sankey Diagram of flows (Anchor -> Regional Blocks -> Partners).
    - Strategic Bilateral Quadrants Matrix (Scatter: Papers vs. Salton Cosine).
    - Scientific Leadership & Sovereignty Balance Bar.
    - Searchable and sortable data table.
    """
    anchor = data["anchor_country_iso3"]
    anchor_name = data["anchor_country_name"]
    doc_title = title or f"Cartografía Geopolítica de Colaboración Científica: {anchor_name} ({anchor})"
    partners = data.get("top_partners", [])
    leadership = data.get("scientific_leadership", {})
    regions = data.get("regional_breakdown", {})

    # Prepare Choropleth data
    choro_locations = [p["partner_country_iso3"] for p in partners]
    choro_z = [p["coauthored_papers"] for p in partners]
    choro_text = [
        f"{p['partner_country_name']} ({p['partner_country_iso3']})<br>Coautorías: {p['coauthored_papers']}<br>Salton: {p['salton_cosine_similarity']}<br>Región: {p['region']}"
        for p in partners
    ]

    # Add Anchor Country in map
    choro_locations.append(anchor)
    choro_z.append(max(choro_z) if choro_z else 10)
    choro_text.append(f"País Ancla: {anchor_name} ({anchor})<br>Total Producción: {data['anchor_total_papers']}")

    # Prepare Sankey Nodes & Links
    # Level 0: Anchor
    # Level 1: Regional Blocks (Iberoamerica, GlobalSouth, OECD, BRICS, Other)
    # Level 2: Top 10 Partners
    sankey_labels = [f"{anchor_name} ({anchor})"]
    sankey_colors = ["#58a6ff"]
    node_index = {anchor: 0}

    # Add regions
    region_keys = ["iberoamerica", "globalsouth", "oecd", "brics"]
    reg_colors = {
        "iberoamerica": "#2ea043",
        "globalsouth": "#f0883e",
        "oecd": "#a371f7",
        "brics": "#f85149"
    }

    for r_k in region_keys:
        r_info = regions.get(r_k, {})
        idx = len(sankey_labels)
        node_index[r_k] = idx
        sankey_labels.append(r_info.get("region_name", r_k.title()))
        sankey_colors.append(reg_colors.get(r_k, "#8b949e"))

    # Add top 12 partners
    top_sankey_partners = partners[:12]
    for p in top_sankey_partners:
        p_iso = p["partner_country_iso3"]
        idx = len(sankey_labels)
        node_index[p_iso] = idx
        sankey_labels.append(f"{p['partner_country_name']} ({p_iso})")
        sankey_colors.append("#388bfd")

    sankey_sources = []
    sankey_targets = []
    sankey_values = []
    sankey_link_colors = []

    # Links: Anchor -> Regions
    for r_k in region_keys:
        r_info = regions.get(r_k, {})
        c_count = r_info.get("collaborations_count", 0)
        if c_count > 0:
            sankey_sources.append(0)
            sankey_targets.append(node_index[r_k])
            sankey_values.append(c_count)
            sankey_link_colors.append("rgba(88, 166, 255, 0.4)")

    # Links: Regions -> Top Partners
    for p in top_sankey_partners:
        p_iso = p["partner_country_iso3"]
        # Find which region it belongs to first
        matched_reg = None
        for r_k in region_keys:
            if p_iso in REGIONAL_GROUPINGS.get(r_k, set()):
                matched_reg = r_k
                break
        if matched_reg and matched_reg in node_index:
            sankey_sources.append(node_index[matched_reg])
            sankey_targets.append(node_index[p_iso])
            sankey_values.append(p["coauthored_papers"])
            sankey_link_colors.append("rgba(46, 160, 67, 0.4)")

    # Prepare Scatter Quadrants data
    scatter_x = [p["coauthored_papers"] for p in partners]
    scatter_y = [p["salton_cosine_similarity"] for p in partners]
    scatter_text = [f"{p['partner_country_name']} ({p['partner_country_iso3']})" for p in partners]
    med_x = sorted(scatter_x)[len(scatter_x)//2] if scatter_x else 1
    med_y = sorted(scatter_y)[len(scatter_y)//2] if scatter_y else 0.1

    # Prepare Leadership data (Top 10 partners)
    lead_partners = partners[:10]
    lead_p_names = [p["partner_country_name"] for p in lead_partners]
    lead_anchor_first = [p["anchor_first_author_count"] for p in lead_partners]
    lead_partner_first = [p["partner_first_author_count"] for p in lead_partners]

    badge_color = "#2ea043" if leadership.get("first_author_rate_pct", 0) >= 50 else ("#f0883e" if leadership.get("first_author_rate_pct", 0) >= 40 else "#f85149")

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{doc_title}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #2ea043;
      --orange: #f0883e;
      --red: #f85149;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
      margin-bottom: 24px;
    }}
    .header h1 {{ font-size: 24px; color: #fff; }}
    .header .subtitle {{ font-size: 14px; color: var(--text-muted); margin-top: 4px; }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 13px;
      color: #fff;
      background: {badge_color};
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }}
    .kpi-title {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi-value {{ font-size: 26px; font-weight: 700; color: #fff; margin: 6px 0; }}
    .kpi-sub {{ font-size: 12px; color: var(--accent); }}
    .chart-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    @media (max-width: 1024px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    .chart-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
    }}
    .chart-card.full-width {{ grid-column: 1 / -1; }}
    .chart-title {{ font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 14px; display: flex; justify-content: space-between; }}
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    th, td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--text-muted); font-weight: 600; background: #1c2128; }}
    tr:hover td {{ background: #21262d; }}
    .filter-input {{
      background: #0d1117;
      border: 1px solid var(--border);
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      margin-bottom: 14px;
      width: 250px;
    }}
  </style>
</head>
<body>

  <div class="header">
    <div>
      <h1>{doc_title}</h1>
      <div class="subtitle">Ecosistema SOS Science of Science • Análisis Geopolítico y Liderazgo Epistemológico</div>
    </div>
    <div>
      <span class="badge">{leadership.get('sovereignty_badge', 'Análisis')}: {leadership.get('first_author_rate_pct', 0)}% 1er Autor</span>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Producción País Ancla</div>
      <div class="kpi-value">{data['anchor_total_papers']:,}</div>
      <div class="kpi-sub">{anchor_name} ({anchor})</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Colaboraciones Internacionales</div>
      <div class="kpi-value">{data['anchor_international_papers']:,}</div>
      <div class="kpi-sub">Tasa Intl: {data['internationalization_rate_pct']}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Países Socios Mapeados</div>
      <div class="kpi-value">{data['total_partner_countries']}</div>
      <div class="kpi-sub">Instancias Bilaterales: {data['total_collaborations_count']}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Tasa de Liderazgo (1er Autor)</div>
      <div class="kpi-value">{leadership.get('first_author_rate_pct', 0)}%</div>
      <div class="kpi-sub">{leadership.get('first_author_led_papers', 0)} papers liderados</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Autor de Correspondencia</div>
      <div class="kpi-value">{leadership.get('corresponding_author_rate_pct', 0)}%</div>
      <div class="kpi-sub">{leadership.get('corresponding_author_led_papers', 0)} artículos</div>
    </div>
  </div>

  <div class="chart-grid">
    <!-- Chart 1: World Map -->
    <div class="chart-card full-width">
      <div class="chart-title">
        <span>Cartografía Global de Coautorías Internacionales</span>
        <span style="font-size:12px; color:var(--text-muted);">Intensidad de Colaboración vs. {anchor_name}</span>
      </div>
      <div id="map-chart" style="height: 480px;"></div>
    </div>

    <!-- Chart 2: Sankey Regional Flows -->
    <div class="chart-card">
      <div class="chart-title">
        <span>Flujos Geopolíticos de Colaboración</span>
        <span style="font-size:12px; color:var(--text-muted);">{anchor} → Bloques → Países</span>
      </div>
      <div id="sankey-chart" style="height: 400px;"></div>
    </div>

    <!-- Chart 3: Quadrants Matrix (Salton vs Papers) -->
    <div class="chart-card">
      <div class="chart-title">
        <span>Matriz Estratégica Bilateral (Salton vs. Volumen)</span>
        <span style="font-size:12px; color:var(--text-muted);">Identificación de Socios Nucleares</span>
      </div>
      <div id="scatter-chart" style="height: 400px;"></div>
    </div>

    <!-- Chart 4: Scientific Leadership Balance -->
    <div class="chart-card full-width">
      <div class="chart-title">
        <span>Balance de Liderazgo Epistemológico por País Socio</span>
        <span style="font-size:12px; color:var(--text-muted);">Primer Autor: {anchor_name} vs. País Contraparte (Top 10)</span>
      </div>
      <div id="leadership-chart" style="height: 340px;"></div>
    </div>
  </div>

  <!-- Data Table -->
  <div class="table-container">
    <div class="chart-title">
      <span>Directorio de Países Socios y Métricas de Afinidad</span>
      <input type="text" id="tableFilter" class="filter-input" placeholder="Filtrar por país o región..." onkeyup="filterTable()">
    </div>
    <table id="partnersTable">
      <thead>
        <tr>
          <th>Rango</th>
          <th>País Socio</th>
          <th>ISO-3</th>
          <th>Región Geopolítica</th>
          <th>Coautorías</th>
          <th>Salton Cosine</th>
          <th>Jaccard</th>
          <th>1er Autor {anchor}</th>
          <th>1er Autor Socio</th>
        </tr>
      </thead>
      <tbody>"""

    for idx, p in enumerate(partners, start=1):
        html += f"""
        <tr>
          <td>#{idx}</td>
          <td><strong>{p['partner_country_name']}</strong></td>
          <td><code>{p['partner_country_iso3']}</code></td>
          <td>{p['region']}</td>
          <td><strong>{p['coauthored_papers']}</strong></td>
          <td>{p['salton_cosine_similarity']:.4f}</td>
          <td>{p['jaccard_similarity']:.4f}</td>
          <td style="color:var(--green);">{p['anchor_first_author_count']}</td>
          <td style="color:var(--orange);">{p['partner_first_author_count']}</td>
        </tr>"""

    html += f"""
      </tbody>
    </table>
  </div>

  <script>
    // 1. World Choropleth Map
    const mapData = [{{
      type: 'choropleth',
      locations: {json.dumps(choro_locations)},
      z: {json.dumps(choro_z)},
      text: {json.dumps(choro_text)},
      hoverinfo: 'text',
      colorscale: 'Blues',
      reversescale: false,
      marker: {{ line: {{ color: '#30363d', width: 0.5 }} }},
      colorbar: {{ title: 'Coautorías', tickfont: {{ color: '#c9d1d9' }}, titlefont: {{ color: '#c9d1d9' }} }}
    }}];
    const mapLayout = {{
      geo: {{
        projection: {{ type: 'natural earth' }},
        showframe: false,
        showcoastlines: true,
        coastlinecolor: '#30363d',
        showland: true,
        landcolor: '#161b22',
        bgcolor: 'rgba(0,0,0,0)',
        subunitcolor: '#30363d'
      }},
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      margin: {{ l: 0, r: 0, t: 0, b: 0 }}
    }};
    Plotly.newPlot('map-chart', mapData, mapLayout, {{ responsive: true, displayModeBar: false }});

    // 2. Geopolitical Sankey
    const sankeyData = [{{
      type: 'sankey',
      orientation: 'h',
      node: {{
        pad: 15,
        thickness: 20,
        line: {{ color: '#30363d', width: 0.5 }},
        label: {json.dumps(sankey_labels)},
        color: {json.dumps(sankey_colors)}
      }},
      link: {{
        source: {json.dumps(sankey_sources)},
        target: {json.dumps(sankey_targets)},
        value: {json.dumps(sankey_values)},
        color: {json.dumps(sankey_link_colors)}
      }}
    }}];
    const sankeyLayout = {{
      font: {{ color: '#c9d1d9', size: 11 }},
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: {{ l: 10, r: 10, t: 10, b: 10 }}
    }};
    Plotly.newPlot('sankey-chart', sankeyData, sankeyLayout, {{ responsive: true, displayModeBar: false }});

    // 3. Bilateral Quadrants Scatter Plot
    const scatterData = [{{
      x: {json.dumps(scatter_x)},
      y: {json.dumps(scatter_y)},
      text: {json.dumps(scatter_text)},
      mode: 'markers+text',
      textposition: 'top center',
      textfont: {{ color: '#8b949e', size: 10 }},
      marker: {{
        size: 10,
        color: '#58a6ff',
        line: {{ color: '#fff', width: 1 }}
      }}
    }}];
    const scatterLayout = {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ color: '#c9d1d9' }},
      xaxis: {{
        title: 'Volumen de Coautorías',
        gridcolor: '#21262d',
        zerolinecolor: '#30363d'
      }},
      yaxis: {{
        title: 'Coseno de Salton Bilateral',
        gridcolor: '#21262d',
        zerolinecolor: '#30363d'
      }},
      shapes: [
        {{ type: 'line', x0: {med_x}, x1: {med_x}, y0: 0, y1: Math.max(...{json.dumps(scatter_y)} || [1]), line: {{ color: '#8b949e', dash: 'dot', width: 1 }} }},
        {{ type: 'line', x0: 0, x1: Math.max(...{json.dumps(scatter_x)} || [1]), y0: {med_y}, y1: {med_y}, line: {{ color: '#8b949e', dash: 'dot', width: 1 }} }}
      ],
      margin: {{ l: 50, r: 20, t: 20, b: 50 }}
    }};
    Plotly.newPlot('scatter-chart', scatterData, scatterLayout, {{ responsive: true, displayModeBar: false }});

    // 4. Leadership Stacked Bar Chart
    const leadData = [
      {{
        name: '{anchor_name} (1er Autor)',
        x: {json.dumps(lead_p_names)},
        y: {json.dumps(lead_anchor_first)},
        type: 'bar',
        marker: {{ color: '#2ea043' }}
      }},
      {{
        name: 'País Socio (1er Autor)',
        x: {json.dumps(lead_p_names)},
        y: {json.dumps(lead_partner_first)},
        type: 'bar',
        marker: {{ color: '#f0883e' }}
      }}
    ];
    const leadLayout = {{
      barmode: 'stack',
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ color: '#c9d1d9' }},
      xaxis: {{ gridcolor: '#21262d' }},
      yaxis: {{ title: 'Artículos en Coautoría', gridcolor: '#21262d' }},
      legend: {{ orientation: 'h', y: 1.15 }},
      margin: {{ l: 50, r: 20, t: 40, b: 60 }}
    }};
    Plotly.newPlot('leadership-chart', leadData, leadLayout, {{ responsive: true, displayModeBar: false }});

    // Table filter function
    function filterTable() {{
      const input = document.getElementById('tableFilter').value.toUpperCase();
      const rows = document.getElementById('partnersTable').getElementsByTagName('tr');
      for (let i = 1; i < rows.length; i++) {{
        const text = rows[i].textContent || rows[i].innerText;
        rows[i].style.display = text.toUpperCase().indexOf(input) > -1 ? '' : 'none';
      }}
    }}
  </script>
</body>
</html>"""
    return html

# ==============================================================================
# 7. CLI COMMAND IMPLEMENTATIONS
# ==============================================================================

def cmd_country_matrix(args):
    """Calculates country co-authorship matrix and Salton cosine index."""
    records = load_corpus(args.input)
    anchor = (args.anchor_country or "MEX").upper()
    analysis = compute_country_analysis(records, anchor_country=anchor, top_n=args.top_n or 25)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"Country matrix generated for {anchor}: {analysis['total_partner_countries']} partners mapped ({analysis['total_collaborations_count']} collabs).")
    print(f"JSON saved to: {args.output}")

    if getattr(args, "html", None):
        html_content = generate_interactive_dashboard_html(analysis, title=getattr(args, "title", None))
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Interactive HTML dashboard saved to: {args.html}")

    sys.exit(0)

def cmd_regional(args):
    """Benchmarks collaboration share across geopolitical regions."""
    matrix_file = args.matrix_file
    if not os.path.exists(matrix_file):
        sys.stderr.write(f"Error: Matrix file does not exist: {matrix_file}\n")
        sys.exit(1)

    with open(matrix_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    region_key = args.region.lower()
    if region_key not in REGIONAL_GROUPINGS:
        sys.stderr.write(f"Error: Unknown region '{args.region}'. Choose from: {list(REGIONAL_GROUPINGS.keys())}\n")
        sys.exit(1)

    region_countries = REGIONAL_GROUPINGS[region_key]
    anchor = (args.anchor_country or data.get("anchor_country_iso3", "MEX")).upper()
    partners = data.get("top_partners", [])

    regional_partners = [p for p in partners if p.get("partner_country_iso3") in region_countries]
    total_regional_collabs = sum(p["coauthored_papers"] for p in regional_partners)
    all_collabs = data.get("total_collaborations_count") or sum(p["coauthored_papers"] for p in partners) or 1
    share_pct = (total_regional_collabs / all_collabs * 100.0)

    result = {
        "anchor_country_iso3": anchor,
        "region_name": args.region.title(),
        "region_member_countries_iso3": sorted(list(region_countries)),
        "regional_collaborations_count": total_regional_collabs,
        "percentage_of_total_collaborations": round(share_pct, 2),
        "regional_partners_breakdown": regional_partners
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Regional benchmark ({args.region}): {total_regional_collabs} collabs ({share_pct:.1f}% share). Saved to {args.output}")
    sys.exit(0)

def cmd_leadership(args):
    """Evaluates scientific leadership by first author and corresponding author status."""
    records = load_corpus(args.input)
    target_country = (args.country or "MEX").upper()
    analysis = compute_country_analysis(records, anchor_country=target_country)
    leadership = analysis.get("scientific_leadership", {})

    result = {
        "country_iso3": target_country,
        "country_name": analysis["anchor_country_name"],
        "total_documents_analyzed": analysis["total_documents_analyzed"],
        "anchor_total_papers": analysis["anchor_total_papers"],
        "total_international_collaborations": analysis["anchor_international_papers"],
        "first_author_led_papers": leadership.get("first_author_led_papers", 0),
        "first_author_leadership_rate_pct": leadership.get("first_author_rate_pct", 0.0),
        "corresponding_author_led_papers": leadership.get("corresponding_author_led_papers", 0),
        "corresponding_author_leadership_rate_pct": leadership.get("corresponding_author_rate_pct", 0.0),
        "sovereignty_status": leadership.get("sovereignty_status", "N/A"),
        "sovereignty_badge": leadership.get("sovereignty_badge", "N/A")
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Leadership for {target_country}: {leadership.get('first_author_rate_pct', 0.0)}% ({leadership.get('sovereignty_status')}).")
    print(f"Saved to {args.output}")
    sys.exit(0)

def cmd_analyze_all(args):
    """Executes full pipeline: country matrix, regional benchmarking, leadership, and HTML dashboard."""
    records = load_corpus(args.input)
    anchor = (args.anchor_country or "MEX").upper()
    analysis = compute_country_analysis(records, anchor_country=anchor, top_n=args.top_n or 30)

    # Export JSON
    os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"Analysis JSON saved to: {args.output_json}")

    # Export CSV
    if getattr(args, "output_csv", None):
        os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
        with open(args.output_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Partner_ISO3", "Partner_Name", "Region", "Coauthored_Papers", "Salton_Cosine", "Jaccard", "Anchor_First_Author", "Partner_First_Author"])
            for idx, p in enumerate(analysis.get("top_partners", []), start=1):
                writer.writerow([
                    idx, p["partner_country_iso3"], p["partner_country_name"], p["region"],
                    p["coauthored_papers"], p["salton_cosine_similarity"], p["jaccard_similarity"],
                    p["anchor_first_author_count"], p["partner_first_author_count"]
                ])
        print(f"Partners CSV saved to: {args.output_csv}")

    # Export HTML Dashboard
    if getattr(args, "html", None):
        html_content = generate_interactive_dashboard_html(analysis, title=getattr(args, "title", None))
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Interactive HTML dashboard saved to: {args.html}")

    sys.exit(0)

# ==============================================================================
# 8. MAIN ENTRYPOINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="CLI for Geopolitical Collaboration Analyst (SOS Ecosystem)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: country-matrix
    p_mat = subparsers.add_parser("country-matrix", help="Generate country co-authorship matrix (ISO-3)")
    p_mat.add_argument("--input", required=True, help="Path to corpus file (.txt, .csv, .parquet, .json)")
    p_mat.add_argument("--anchor-country", default="MEX", help="Anchor country ISO-3 (default: MEX)")
    p_mat.add_argument("--top-n", type=int, default=25, help="Number of top partners to output")
    p_mat.add_argument("--html", help="Path to output standalone interactive HTML dashboard")
    p_mat.add_argument("--title", help="Optional title for the dashboard")
    p_mat.add_argument("--output", required=True, help="Path to output JSON")
    p_mat.set_defaults(func=cmd_country_matrix)

    # Subcommand: regional-benchmark
    p_reg = subparsers.add_parser("regional-benchmark", help="Benchmark across geopolitical regions")
    p_reg.add_argument("--matrix-file", required=True, help="Path to country matrix JSON from country-matrix")
    p_reg.add_argument("--region", choices=["iberoamerica", "globalsouth", "oecd", "brics", "european_union", "Iberoamerica", "GlobalSouth", "OECD", "BRICS"], required=True)
    p_reg.add_argument("--anchor-country", default="MEX", help="Anchor country ISO-3")
    p_reg.add_argument("--output", required=True, help="Path to output JSON")
    p_reg.set_defaults(func=cmd_regional)

    # Subcommand: scientific-leadership
    p_lea = subparsers.add_parser("scientific-leadership", help="Calculate first & corresponding author leadership in international papers")
    p_lea.add_argument("--input", required=True, help="Path to corpus file (.txt, .csv, .parquet, .json)")
    p_lea.add_argument("--country", default="MEX", help="Target country ISO-3 (default: MEX)")
    p_lea.add_argument("--output", required=True, help="Path to output JSON")
    p_lea.set_defaults(func=cmd_leadership)

    # Subcommand: analyze-all
    p_all = subparsers.add_parser("analyze-all", help="Execute complete pipeline: matrix, regional benchmark, leadership, CSV, and HTML dashboard")
    p_all.add_argument("--input", required=True, help="Path to corpus file (.txt, .csv, .parquet, .json)")
    p_all.add_argument("--anchor-country", default="MEX", help="Anchor country ISO-3 (default: MEX)")
    p_all.add_argument("--top-n", type=int, default=30, help="Number of top partners")
    p_all.add_argument("--output-json", required=True, help="Path to output JSON")
    p_all.add_argument("--output-csv", help="Path to output partners CSV")
    p_all.add_argument("--html", help="Path to output interactive HTML dashboard")
    p_all.add_argument("--title", help="Optional title for dashboard")
    p_all.set_defaults(func=cmd_analyze_all)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
