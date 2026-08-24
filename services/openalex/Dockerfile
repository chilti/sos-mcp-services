FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/openalex/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/openalex ./services/openalex
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8006"
EXPOSE 8006
CMD ["python", "services/openalex/mcp_server.py"]
