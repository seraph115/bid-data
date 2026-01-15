FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (e.g., for mysqlclient if needed, or gcc)
# pure python dependencies don't strictly need system libraries usually
# RUN apt-get update && apt-get install -y --no-install-recommends ...

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command to keep container running or run spider
# For distributed, we might want to just run the spider expecting tasks in Redis,
# or run it once.
CMD ["scrapy", "crawl", "jl_zfcg"]
