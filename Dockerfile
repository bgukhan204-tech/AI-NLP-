FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render supplies the PORT environment variable for web services.
# Streamlit is started on that port so Render's proxy can reach the app.
CMD ["sh", "-c", "python scripts/generate_oidc_secrets.py && exec streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8501}"]
