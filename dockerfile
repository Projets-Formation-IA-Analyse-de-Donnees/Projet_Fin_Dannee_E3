FROM python:3.10-slim

WORKDIR /code

COPY . /code/

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "run.py"]  


