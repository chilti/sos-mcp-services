# SOS MCP Shared Module
from shared.config import settings
from shared.canonical_schema import (
    CANONICAL_COLUMNS,
    normalize_record_to_canonical,
    save_canonical_corpus,
    create_empty_canonical_dataframe
)
from shared.duckdb_engine import (
    get_duckdb_connection,
    execute_corpus_query,
    aggregate_corpus_by_year,
    aggregate_corpus_oa_distribution,
    get_corpus_top_authors,
    extract_coauthorship_graph,
    calculate_lotka_law_fit
)
