FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY services/topics/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r service_requirements.txt
COPY shared ./shared
COPY services/topics ./services/topics
ENV PYTHONPATH="/app"
ENV MCP_TRANSPORT="http"
ENV PORT="8005"
EXPOSE 8005
CMD ["python", "services/topics/mcp_server.py"]
