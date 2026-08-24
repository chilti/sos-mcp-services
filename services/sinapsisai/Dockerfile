FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/sinapsisai/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/sinapsisai ./services/sinapsisai
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8002"
EXPOSE 8002
CMD ["python", "services/sinapsisai/mcp_server.py"]
