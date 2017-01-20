FROM node

ARG HOST

# Install NGINX
ENV NGINX_VERSION 1.11.8-1~jessie

RUN apt-key adv --keyserver hkp://pgp.mit.edu:80 --recv-keys 573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62 \
	&& echo "deb http://nginx.org/packages/mainline/debian/ jessie nginx" >> /etc/apt/sources.list \
	&& apt-get update \
	&& apt-get install --no-install-recommends --no-install-suggests -y \
						ca-certificates \
						nginx=${NGINX_VERSION} \
						nginx-module-xslt \
						nginx-module-geoip \
						nginx-module-image-filter \
						nginx-module-perl \
						nginx-module-njs \
						gettext-base \
	&& rm -rf /var/lib/apt/lists/*

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log
RUN mkdir -p /var/www/predots/public

# Configure frontend
RUN npm install -g grunt-cli bower
COPY . /setup
WORKDIR /setup
RUN npm install
RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN bower install
RUN grunt buildProd --out=/var/www/predots/public

# Configure NGINX
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
RUN envsubst '$$HOST' < /etc/nginx/conf.d/nginx.conf > /etc/nginx/conf.d/default.conf


EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
