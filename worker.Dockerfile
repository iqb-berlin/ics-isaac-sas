FROM python:3.11

RUN mkdir /iscs

WORKDIR /iscs

COPY src ./

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["rq", "worker"]
