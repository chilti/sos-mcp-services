# Elsevier Quota Policies and HTTP 429 Responses

Elsevier enforces rate limits and weekly/monthly quotas on API keys registered in the Elsevier Developer Portal.

---

## 1. Typical Scopus API Limits

- **Rate per second:** Typically 2 to 5 requests per second for standard licenses.
- **Weekly quota:** Depends on the institutional subscription tier (Institutional Subscription vs. Non-Commercial Free tier).
- **Batch size (`count`):** The maximum allowed in a single search request is 25 for standard views and 10 for complete views.

---

## 2. Handling HTTP 429 Errors (Too Many Requests)

When the burst or temporary quota is exhausted:
1. The server returns status code `429 Too Many Requests`.
2. The CLI client automatically detects status code 429.
3. A 5-second backoff pause is applied before retrying the request.
4. If the institutional monthly quota is completely exhausted, a warning is written to `stderr` to alert the agent.
