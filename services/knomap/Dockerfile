FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/knomap/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/knomap ./services/knomap
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8001"
EXPOSE 8001
CMD ["python", "services/knomap/mcp_server.py"]
