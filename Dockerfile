FROM nikriek/python3-java-ml:latest
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /setup/
RUN pip3 install -r /setup/requirements.txt

# Setup private key for repository access
COPY credentials/id_rsa.rar /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa
RUN echo "Host github.com\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config

# Setup rar-mfs algorithm
RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://dl.bintray.com/sbt/debian /" | tee -a /etc/apt/sources.list.d/sbt.list
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2EE0EA64E40A89B84B2DF73499E82A75642AC823
RUN apt-get update
RUN apt-get install -y git sbt
WORKDIR /setup
RUN git clone git@github.com:KDD-OpenSource/rar-mfs.git
WORKDIR /setup/rar-mfs
RUN sbt assembly
RUN mkdir /assets
RUN cp target/scala-2.11/rar-mfs-assembly-1.0.1.jar /assets/rar-mfs.jar

VOLUME /code
WORKDIR /code
COPY . /code
