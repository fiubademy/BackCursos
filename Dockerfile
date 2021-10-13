FROM ubuntu

EXPOSE 8003

RUN apt-get -y update 
RUN apt-get -y install python3
RUN apt-get -y install python3-pip

WORKDIR /app

COPY requirements.txt /app/
COPY service/CourseService.py /app/

RUN pip3 install -r requirements.txt
CMD python3 CourseService.py