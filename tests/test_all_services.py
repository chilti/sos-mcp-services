import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 1. Test PLmetrix Tools
from services.plmetrix.tools.laws_tools import (
    analyze_lotka_law,
    analyze_bradford_law,
    analyze_price_index,
    analyze_scientific_growth_phases
)

lotka_res = analyze_lotka_law([1, 1, 1, 1, 1, 2, 2, 3, 5, 10])
assert lotka_res.get("lotka_exponent_c") is not None, "Lotka test failed"

bradford_res = analyze_bradford_law([{"journal": "J1", "articles": 50}, {"journal": "J2", "articles": 20}, {"journal": "J3", "articles": 10}])
assert bradford_res.get("total_articles") == 80, "Bradford test failed"

price_res = analyze_price_index([2023, 2022, 2020, 2015, 2010], publication_year=2024)
assert price_res.get("price_index_percentage") is not None, "Price test failed"

growth_res = analyze_scientific_growth_phases([2015, 2016, 2017, 2018, 2019, 2020], [10, 15, 24, 38, 60, 95])
assert growth_res.get("current_maturity_phase") is not None, "Growth test failed"

# 2. Test RevistasLATAM Tools
from services.revistaslatam.tools.journals_tools import (
    get_journal_impact_profile,
    compare_journals_benchmarking,
    analyze_country_editorial_landscape
)
j_res = get_journal_impact_profile("1234-5678")
assert j_res.get("metrics", {}).get("mean_fwci") == 1.18, "RevistasLATAM test failed"

# 3. Test Topics Tools
from services.topics.tools.fronts_tools import detect_research_fronts_multimodal
from services.topics.tools.geopolitics_tools import get_geopolitical_collaboration_matrix
rf_res = detect_research_fronts_multimodal("Artificial Intelligence")
assert rf_res.get("total_fronts_detected") == 4, "Topics fronts test failed"

# 4. Test SinapsisAI Tools
from services.sinapsisai.tools.snii_tools import resolve_snii_identity
snii_res = resolve_snii_identity("Rafael Torres Córdoba", "UNAM")
assert snii_res.get("canonical_match", {}).get("official_snii_name") is not None, "SinapsisAI SNII test failed"

# 5. Test knoMap SOM & InCites Tools
from services.knomap.tools.som_tools import suggest_grid_size
som_sug = suggest_grid_size([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
assert som_sug.get("small_som_recommendation") is not None, "knoMap SOM test failed"

print("[OK] Todos los tests unitarios de los 6 microservicios pasaron exitosamente.")
