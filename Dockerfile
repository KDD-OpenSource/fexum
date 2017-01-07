FROM nikriek/python3-java-ml:latest
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /setup/
RUN pip3 install -r /setup/requirements.txt

VOLUME /code
WORKDIR /code
COPY . /code
