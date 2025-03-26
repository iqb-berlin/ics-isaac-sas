FROM tiangolo/uvicorn-gunicorn:python3.11
COPY src /app
COPY data /data
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install pydevd-pycharm==243.26053.29
