FROM python:3.8.0-slim-buster
LABEL team="development" \
      maintainer="Ian" \
      email="ian@widgets.com"
MAINTAINER "ian@widgets.com"
RUN apt-get update \
&& apt-get install gcc python3-dev musl-dev -y \
&& apt-get clean
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --user -r requirements.txt
COPY carLister/ /app
EXPOSE 8080
ENTRYPOINT [ "python3" ]
CMD [ "main.py" ]