# ISO-3166-1 Normalization Dictionary and Geopolitical Taxonomy

Formal standardization of country codes and regional analytical blocs for scientometric mapping and international science diplomacy.

---

## 1. Canonical Mapping of Codes and Geopolitical Regions

| Country / Territory | ISO Alpha-3 | ISO Alpha-2 | Primary Region | Analytical Blocs |
|:---|:---:|:---:|:---|:---|
| **Mexico** | `MEX` | `MX` | North America | Ibero-America, OECD, Global South |
| **Spain** | `ESP` | `ES` | Western Europe | Ibero-America, European Union, OECD |
| **Brazil** | `BRA` | `BR` | South America | Ibero-America, BRICS, Global South |
| **Argentina** | `ARG` | `AR` | South America | Ibero-America, Global South |
| **Chile** | `CHL` | `CL` | South America | Ibero-America, OECD, Global South |
| **Colombia** | `COL` | `CO` | South America | Ibero-America, OECD, Global South |
| **Peru** | `PER` | `PE` | South America | Ibero-America, Global South |
| **Uruguay** | `URY` | `UY` | South America | Ibero-America, Global South |
| **Cuba** | `CUB` | `CU` | Caribbean | Ibero-America, Global South |
| **Ecuador** | `ECU` | `EC` | South America | Ibero-America, Global South |
| **Costa Rica** | `CRI` | `CR` | Central America | Ibero-America, OECD, Global South |
| **Panama** | `PAN` | `PA` | Central America | Ibero-America, Global South |
| **Bolivia** | `BOL` | `BO` | South America | Ibero-America, Global South |
| **Venezuela** | `VEN` | `VE` | South America | Ibero-America, Global South |
| **Portugal** | `PRT` | `PT` | Western Europe | Ibero-America, European Union, OECD |
| **United States** | `USA` | `US` | North America | OECD |
| **Canada** | `CAN` | `CA` | North America | OECD |
| **United Kingdom** | `GBR` | `GB` | Europe | OECD (England, Scotland, Wales, N. Ireland) |
| **Germany** | `DEU` | `DE` | Central Europe | European Union, OECD |
| **France** | `FRA` | `FR` | Western Europe | European Union, OECD |
| **Italy** | `ITA` | `IT` | Southern Europe | European Union, OECD |
| **Netherlands** | `NLD` | `NL` | Western Europe | European Union, OECD |
| **Switzerland** | `CHE` | `CH` | Central Europe | OECD |
| **China** | `CHN` | `CN` | East Asia | BRICS (includes Peoples R China, PR China) |
| **Japan** | `JPN` | `JP` | East Asia | OECD |
| **South Korea** | `KOR` | `KR` | East Asia | OECD |
| **India** | `IND` | `IN` | South Asia | BRICS, Global South |
| **Russia** | `RUS` | `RU` | Eurasia | BRICS |
| **South Africa** | `ZAF` | `ZA` | Southern Africa | BRICS, Global South |
| **Egypt** | `EGY` | `EG` | North Africa / Middle East | BRICS, Global South |
| **Australia** | `AUS` | `AU` | Oceania | OECD |

---

## 2. Taxonomy of Formal Geopolitical Blocs

The quantitative engine groups countries into five science-policy macro-blocs:

1. **`Iberoamerica` (22 countries):**
   * Full members of the OEI and Ibero-American Summits (Spanish- and Portuguese-speaking Latin America + Spain, Portugal, and Andorra).
   * Key indicator: linguistic cohesion and circulation in regional indexed journals (SciELO, Redalyc, Latindex).
2. **`GlobalSouth` (Global South):**
   * Grouping of developing economies across Latin America, Africa, the Indian subcontinent, and Southeast Asia.
   * Key indicator: South-South cooperation unmediated by Global North metropolises.
3. **`OECD` (38 countries):**
   * Consolidated scientific-technological and industrial powers (North America, Western Europe, Japan, South Korea, Australia, etc.).
4. **`BRICS` (10 consolidated and expanded countries):**
   * Brazil, Russia, India, China, South Africa, Egypt, Ethiopia, Iran, United Arab Emirates, and Saudi Arabia.
5. **`EuropeanUnion` (27 EU member states):**
   * Ecosystem articulated under the Horizon Europe framework programs.

---

## 3. Disambiguation Rules and Extraction Heuristics

1. **Historical and Compound Names:**
   * `Peoples R China`, `P.R. China`, `PR China` $\to$ `CHN`.
   * `England`, `Scotland`, `Wales`, `Northern Ireland` $\to$ `GBR`.
   * `Fed Rep Germany`, `Federal Republic of Germany` $\to$ `DEU`.
   * `South Korea`, `Republic of Korea` $\to$ `KOR`.
   * `Netherlands`, `The Netherlands`, `Holland` $\to$ `NLD`.
2. **Affiliations with Postal Codes:**
   * Strings such as `Suwon 16419, South Korea.` or `Honolulu, HI 96822 USA.` resolve the country code by scanning terminal tokens without confusing state/city abbreviations with an ISO code.
3. **Prohibition of Blind Truncation:**
   * No text is truncated to its first 3 characters if it does not match a registered code or synonym. If a string does not correspond to a recognized sovereign country or territory, it is discarded to prevent false positives (e.g., Chinese provinces or intermediate cities).
