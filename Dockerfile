FROM python:3.13.5-slim

WORKDIR /url

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app","--host","0.0.0.0","--port","8000"]