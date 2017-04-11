FROM nikriek/python3-ml:latest
ENV PYTHONUNBUFFERED 1

# Install dependencies for ccwt package
RUN apt-get install -y libfftw3-dev libpng-dev

# Setup private key for repository access
COPY credentials/hics-pip.rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa
RUN echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

COPY requirements.txt /setup/
RUN pip3 install -r /setup/requirements.txt

VOLUME /code
WORKDIR /code
COPY . /code
