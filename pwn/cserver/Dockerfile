FROM ubuntu@sha256:b4b521bfcec90b11d2869e00fe1f2380c21cbfcd799ee35df8bd7ac09e6f63ea
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -y \
    cgroup-tools sudo gcc-multilib xinetd coreutils vim && \
        apt-get clean autoclean && \
        apt-get autoremove --yes && \
        rm -rf /var/lib/{apt,dpkg,cache,log}/


RUN mkdir -p /pwnpeii/scripts /pwnpeii/challenge-files
WORKDIR /pwnpeii

COPY pwnpeii/scripts/cleanup.sh /pwnpeii/scripts
COPY pwnpeii/scripts/runner.sh /pwnpeii/scripts

COPY pwnpeii/configs/limits.conf /etc/security/limits.conf
COPY pwnpeii/configs/sysctl.conf /etc/sysctl.conf

RUN groupadd problemusers
RUN useradd -m -G problemusers problemuser

WORKDIR /home/problemuser
COPY pwnpeii/start.sh /pwnpeii/start.sh

COPY flag.txt .

COPY src/chall ./chall
RUN chmod +x ./chall

CMD ["/pwnpeii/start.sh"]
