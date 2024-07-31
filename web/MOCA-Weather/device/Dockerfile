FROM linuxserver/openssh-server

RUN apk update && apk add python3

RUN useradd -ms /bin/bash target
COPY flag.txt /flag.txt

RUN chown root:root /flag.txt
RUN chmod 444 /flag.txt

COPY ./cpu_temp /usr/bin/cpu_temp
COPY ./humidity /usr/bin/humidity
COPY ./temp /usr/bin/temp
 
RUN chmod +x /usr/bin/cpu_temp /usr/bin/humidity /usr/bin/temp