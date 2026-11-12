# Guide to JOIN-Free Query Patterns for Mexico in ClickHouse

## Performance Principles

1. **Leverage MergeTree:** The `rag.works_academic_all` table is ordered by primary key. Whenever possible, include partition/sorting filters such as `publication_year` in the `WHERE` clause to activate *block skipping*.
2. **Vectorized Array Functions:**
   - For exact membership in lists: `has(array, 'value')`.
   - For substring or pattern matching in arrays: `arrayExists(x -> positionCaseInsensitiveUTF8(x, 'pattern') > 0, array)`.
3. **Bounded `IN` Subqueries Instead of JOINs:**
   If filtering publications from a list of authors or identifiers is indispensable:
   ```sql
   -- CORRECT: Simple subquery with LIMIT
   SELECT title, cited_by_count
   FROM rag.works_academic_all
   WHERE id IN (
       SELECT id FROM rag.works_seed_mexico WHERE publication_year = 2024 LIMIT 1000
   )
   
   -- PROHIBITED: Direct JOIN between large tables
   SELECT w.title FROM rag.works_academic_all w JOIN rag.works_seed_mexico s ON w.id = s.id
   ```
