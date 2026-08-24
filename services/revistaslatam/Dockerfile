FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/revistaslatam/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/revistaslatam ./services/revistaslatam
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8004"
EXPOSE 8004
CMD ["python", "services/revistaslatam/mcp_server.py"]
