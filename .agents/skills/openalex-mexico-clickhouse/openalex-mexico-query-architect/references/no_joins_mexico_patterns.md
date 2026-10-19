# Guía de Patrones de Consulta sin JOINs para México en ClickHouse

## Principios de Rendimiento

1. **Aprovechar MergeTree:** La tabla `rag.works_academic_all` está ordenada por clave primaria. Incluir siempre que sea posible filtros de partición como `publication_year` en la cláusula `WHERE` para activar la poda de bloques (*block skipping*).
2. **Funciones de Array Vectorizadas:**
   - Para pertenencia exacta en listas: `has(array, 'valor')`.
   - Para búsqueda de subcadenas o patrones en arrays: `arrayExists(x -> positionCaseInsensitiveUTF8(x, 'patron') > 0, array)`.
3. **Subconsultas IN con Límite en vez de JOINs:**
   Si es indispensable filtrar publicaciones a partir de una lista de autores o identificadores:
   ```sql
   -- CORRECTO: Subquery simple con LIMIT
   SELECT title, cited_by_count
   FROM rag.works_academic_all
   WHERE id IN (
       SELECT id FROM rag.works_seed_mexico WHERE publication_year = 2024 LIMIT 1000
   )
   
   -- PROHIBIDO: JOIN directo entre tablas grandes
   SELECT w.title FROM rag.works_academic_all w JOIN rag.works_seed_mexico s ON w.id = s.id
   ```
