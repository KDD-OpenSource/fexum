FROM nikriek/python3-ml:latest
ENV PYTHONUNBUFFERED 1

# Install dependencies for ccwt package
RUN apt-get update
RUN apt-get install -y libfftw3-dev libpng-dev

COPY requirements.txt /setup/
RUN pip3 install -r /setup/requirements.txt

VOLUME /code
WORKDIR /code
COPY . /code
