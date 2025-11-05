FROM python:3.10-slim
WORKDIR /app

# install curl required by compose healthcheck (and keep image small)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# generate data and train model on build
RUN python src/generate_synthetic.py && python src/train.py

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8001", "--loop", "uvloop"]
