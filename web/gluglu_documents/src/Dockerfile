# Build frontend
FROM node@sha256:7ce8b205d15e30fd395e5fa4000bcdf595fcff3f434fe75822e54e82a5f5cf82 as build-frontend

# Move dependencies and install them
WORKDIR /app
COPY ./gluglu_frontend/package*.json ./
RUN npm install

# Build frontend
COPY ./gluglu_frontend/. ./
RUN npm run build




# Actual deployment
FROM node:18.13
#FROM trafex/php-nginx

RUN apt update -y
RUN apt install -y ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils libxshmfence1 libglu1 cron

# Install nginx and php
RUN apt-get update && apt-get install -y nginx php-fpm
RUN mkdir /run/php/

# Move nginx configuration
COPY nginx/default.conf /etc/nginx/sites-enabled/default

RUN rm -rf /var/www/html/*

WORKDIR /var/www/html

# move frontend in public directory
COPY --from=build-frontend /app/build ./

# Move php backend in the root directory
COPY ./gluglu_backend/ ./

RUN chmod 555 -R /var/www/html
RUN mkdir /var/www/html/upload_your_shell_here
RUN chmod 777 /var/www/html/upload_your_shell_here

# Move flag and set permissions
COPY ./flag.txt /flag.txt
RUN chmod 400 /flag.txt

COPY readflag.c /readflag.c
RUN gcc /readflag.c -o /readflag
RUN chmod 555 /readflag

# Add suid bit to readflag
RUN chmod +s /readflag

# Move renderer dependencies and install them
WORKDIR /var/www/html/app
COPY ./gluglu_pdf_worker/package*.json ./
RUN npm install

# Move renderer code
COPY ./gluglu_pdf_worker/app.js ./

# Prepare cron-job
COPY cronjob /cronjob
RUN crontab /cronjob

COPY ./init.sh /init.sh

CMD ["bash", "/init.sh"]