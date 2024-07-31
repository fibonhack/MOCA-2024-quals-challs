#!/bin/sh

# Creating dummy user
useradd -m -s /bin/sh "dummy"

# Start php fpm
php-fpm7.4 &

# Run nginx
nginx -g 'daemon off;' &

# Run crontab
cron &

# Wait
sleep infinity