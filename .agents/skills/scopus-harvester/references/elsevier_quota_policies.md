# Políticas de Cuota y Respuestas HTTP 429 de Elsevier

Elsevier aplica límites de tasa y cuotas semanales/mensuales sobre las claves de API registradas en el Portal de Desarrolladores de Elsevier.

---

## 1. Límites Típicos de la API de Scopus

- **Frecuencia por segundo:** Típicamente entre 2 a 5 solicitudes por segundo para licencias estándar.
- **Límite semanal:** Depende del nivel de suscripción institucional (Institutional Subscription vs Non-Commercial Free tier).
- **Tamaño de lote (`count`):** El máximo permitido en una sola llamada de búsqueda es 25 para vistas estándar y 10 para vistas completas.

---

## 2. Gestión de Errores HTTP 429 (Too Many Requests)

Cuando la cuota temporal o de ráfaga se agota:
1. El servidor devuelve código de estado `429 Too Many Requests`.
2. El cliente CLI detecta automáticamente el código 429.
3. Se aplica una pausa de espera exponencial (backoff de 5 segundos) antes de reintentar la solicitud.
4. Si la cuota mensual institucional está completamente agotada, se notifica en `stderr` para advertir al agente.
