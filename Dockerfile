FROM ubuntu

EXPOSE 8003

RUN apt-get -y update 
RUN apt-get -y install python3
RUN apt-get -y install python3-pip

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app/

RUN pip3 install -r requirements.txt
CMD python3 src/app/main.py
