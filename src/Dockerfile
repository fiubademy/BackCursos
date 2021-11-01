FROM ubuntu

EXPOSE 8003

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /usr/src/app/requirements.txt
COPY . /usr/src/app/

RUN pip3 install -r requirements.txt
CMD python3 main.py