FROM python:3.11

RUN mkdir /data
RUN mkdir /data/bow_models
RUN mkdir /data/model_metrics
RUN mkdir /data/onnx_models

RUN mkdir /ics-is
WORKDIR /ics-is
COPY src ./

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["rq", "worker"]
