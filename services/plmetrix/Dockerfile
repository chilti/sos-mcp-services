FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/plmetrix/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/plmetrix ./services/plmetrix
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8003"
EXPOSE 8003
CMD ["python", "services/plmetrix/mcp_server.py"]
