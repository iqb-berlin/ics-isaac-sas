FROM python:3.11

RUN mkdir /data
RUN mkdir /data/bow_models
RUN mkdir /data/model_metrics
RUN mkdir /data/onnx_models
RUN mkdir /data/instructions

COPY ics /app/ics
COPY lib /app/lib

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["rq", "worker"]
