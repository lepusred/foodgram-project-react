FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip wheel
RUN pip install -r ./requirements.txt --no-cache-dir
COPY ./ ./
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000"]