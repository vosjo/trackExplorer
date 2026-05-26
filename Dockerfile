FROM python:3.12-slim

WORKDIR /app

RUN useradd -m -u 1000 user

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p trackExplorer/downloads && chown -R user:user /app

USER user

EXPOSE 7860

CMD python -c "import os; open('google-credentials.json','w').write(os.environ.get('GOOGLE_CREDENTIALS','{}'))" && gunicorn trackExplorer.trackExplorer:app --bind 0.0.0.0:7860 --timeout 120
