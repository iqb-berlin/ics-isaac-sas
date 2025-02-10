FROM tiangolo/uvicorn-gunicorn:python3.7
ADD src /app
ADD data /data
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
