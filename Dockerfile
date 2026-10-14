# Build the wheel first with: python scripts/release.py build
# This image installs that wheel. It never rebuilds or copies application source.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY dist/*.whl /tmp/wheels/
RUN python -m pip install --no-cache-dir --no-index --no-deps /tmp/wheels/*.whl \
    && rm -rf /tmp/wheels \
    && useradd --create-home --uid 10001 demo

USER demo
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["python", "-I", "-m", "cicd_demo", "--host", "0.0.0.0", "--port", "8000"]
