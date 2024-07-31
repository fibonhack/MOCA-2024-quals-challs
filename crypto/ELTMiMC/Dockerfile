FROM sagemath/sagemath:10.1

USER root
RUN apt-get update
RUN apt-get install -y socat git
RUN sage -pip install pycryptodome

COPY src/ELTMiMC.py /app/ELTMiMC.py
COPY src/flag.txt /app/flag.txt

WORKDIR /app
ENTRYPOINT ["socat", "-t", "900", "-T", "120", "TCP4-LISTEN:5555,reuseaddr,fork", "EXEC:env PYTHONUNBUFFERED=1 sage -python /app/ELTMiMC.py"]
