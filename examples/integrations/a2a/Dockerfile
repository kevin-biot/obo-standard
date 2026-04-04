FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agents.py .
# Default: TravelAgent demo mode. Override with --server for FlightSearchAgent.
ENTRYPOINT ["python", "agents.py"]
CMD ["--demo"]
