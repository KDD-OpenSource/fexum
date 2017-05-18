FROM nginx:latest

RUN mkdir -p /setup
WORKDIR /setup

# Install node
RUN apt-get update
RUN apt-get install -y curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs

# Install git
RUN apt-get install -y git-core

# Configure frontend
RUN git clone git@github.com:KDD-OpenSource/fexum-frontend.git
WORKDIR /setup/fexum-frontend
RUN npm install -g grunt-cli bower
RUN npm install
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN bower install --quiet --silent
RUN grunt buildProd --out=/var/www/fexum/public > /dev/null

# Configure NGINX
WORKDIR /setup
COPY nginx.conf /setup

EXPOSE 80 443
