# Diccionario de Normalización y Taxonomía Geopolítica ISO-3166-1

Estandarización formal de códigos de país y bloques analíticos regionales para cartografía cienciométrica y diplomacia científica internacional.

---

## 1. Mapeo Canónico de Códigos y Regiones Geopolíticas

| País / Territorio | ISO Alpha-3 | ISO Alpha-2 | Región Principal | Bloques Analíticos |
|:---|:---:|:---:|:---|:---|
| **México** | `MEX` | `MX` | América del Norte | Iberoamérica, OCDE, Sur Global |
| **España** | `ESP` | `ES` | Europa Occidental | Iberoamérica, Unión Europea, OCDE |
| **Brasil** | `BRA` | `BR` | América del Sur | Iberoamérica, BRICS, Sur Global |
| **Argentina** | `ARG` | `AR` | América del Sur | Iberoamérica, Sur Global |
| **Chile** | `CHL` | `CL` | América del Sur | Iberoamérica, OCDE, Sur Global |
| **Colombia** | `COL` | `CO` | América del Sur | Iberoamérica, OCDE, Sur Global |
| **Perú** | `PER` | `PE` | América del Sur | Iberoamérica, Sur Global |
| **Uruguay** | `URY` | `UY` | América del Sur | Iberoamérica, Sur Global |
| **Cuba** | `CUB` | `CU` | Caribe | Iberoamérica, Sur Global |
| **Ecuador** | `ECU` | `EC` | América del Sur | Iberoamérica, Sur Global |
| **Costa Rica** | `CRI` | `CR` | América Central | Iberoamérica, OCDE, Sur Global |
| **Panamá** | `PAN` | `PA` | América Central | Iberoamérica, Sur Global |
| **Bolivia** | `BOL` | `BO` | América del Sur | Iberoamérica, Sur Global |
| **Venezuela** | `VEN` | `VE` | América del Sur | Iberoamérica, Sur Global |
| **Portugal** | `PRT` | `PT` | Europa Occidental | Iberoamérica, Unión Europea, OCDE |
| **Estados Unidos** | `USA` | `US` | América del Norte | OCDE |
| **Canadá** | `CAN` | `CA` | América del Norte | OCDE |
| **Reino Unido** | `GBR` | `GB` | Europa | OCDE (Inglaterra, Escocia, Gales, I. del Norte) |
| **Alemania** | `DEU` | `DE` | Europa Central | Unión Europea, OCDE |
| **Francia** | `FRA` | `FR` | Europa Occidental | Unión Europea, OCDE |
| **Italia** | `ITA` | `IT` | Europa Meridional | Unión Europea, OCDE |
| **Países Bajos** | `NLD` | `NL` | Europa Occidental | Unión Europea, OCDE |
| **Suiza** | `CHE` | `CH` | Europa Central | OCDE |
| **China** | `CHN` | `CN` | Asia Oriental | BRICS (incluye Peoples R China, PR China) |
| **Japón** | `JPN` | `JP` | Asia Oriental | OCDE |
| **Corea del Sur** | `KOR` | `KR` | Asia Oriental | OCDE |
| **India** | `IND` | `IN` | Asia Meridional | BRICS, Sur Global |
| **Rusia** | `RUS` | `RU` | Eurasia | BRICS |
| **Sudáfrica** | `ZAF` | `ZA` | África Austral | BRICS, Sur Global |
| **Egipto** | `EGY` | `EG` | Norte de África / M. Oriente | BRICS, Sur Global |
| **Australia** | `AUS` | `AU` | Oceanía | OCDE |

---

## 2. Taxonomía de Bloques Geopolíticos Formales

El motor cuantitativo agrupa los países en cinco macro-bloques de política científica:

1. **`Iberoamerica` (22 países):**
   * Miembros plenos de la OEI y Cumbres Iberoamericanas (Latinoamérica de habla hispana y portuguesa + España, Portugal y Andorra).
   * Indicador clave: cohesión lingüística y circulación en revistas indexadas regionales (SciELO, Redalyc, Latindex).
2. **`GlobalSouth` (Sur Global):**
   * Agrupación de economías en desarrollo de América Latina, África, el subcontinente indio y el Sudeste Asiático.
   * Indicador clave: cooperación Sur-Sur no mediada por las metrópolis del Norte Global.
3. **`OECD` (OCDE - 38 países):**
   * Potencias científico-tecnológicas e industriales consolidadas (Norteamérica, Europa Occidental, Japón, Corea del Sur, Australia, etc.).
4. **`BRICS` (10 países consolidados y ampliados):**
   * Brasil, Rusia, India, China, Sudáfrica, Egipto, Etiopía, Irán, Emiratos Árabes Unidos y Arabia Saudita.
5. **`EuropeanUnion` (27 estados miembros de la UE):**
   * Ecosistema articulado bajo los programas marco Horizon Europe.

---

## 3. Reglas de Desambiguación y Heurísticas de Extracción

1. **Nombres Históricos y Compuestos:**
   * `Peoples R China`, `P.R. China`, `PR China` $\to$ `CHN`.
   * `England`, `Scotland`, `Wales`, `Northern Ireland` $\to$ `GBR`.
   * `Fed Rep Germany`, `Federal Republic of Germany` $\to$ `DEU`.
   * `South Korea`, `Republic of Korea` $\to$ `KOR`.
   * `Netherlands`, `The Netherlands`, `Holland` $\to$ `NLD`.
2. **Afiliaciones con Código Postal:**
   * Cadenas como `Suwon 16419, South Korea.` o `Honolulu, HI 96822 USA.` resuelven el código de país buscando los tokens terminales sin confundir el estado/ciudad con un código ISO.
3. **Prohibición de Truncación Ciega:**
   * Ningún texto se truncará a sus primeros 3 caracteres si no coincide con un código o sinónimo registrado. Si una cadena no corresponde a un país soberano o territorio reconocido, se descarta para evitar la creación de falsos positivos (e.g. provincias chinas o ciudades intermedias).
