FROM tiangolo/uvicorn-gunicorn:python3.11
COPY src /app
RUN mkdir /data
RUN mkdir /data/bow_models
RUN mkdir /data/model_metrics
RUN mkdir /data/onnx_models
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install pydevd-pycharm==243.26053.29
