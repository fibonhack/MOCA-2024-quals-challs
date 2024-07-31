# Use the official Node.js image as the base image
FROM node:18

RUN apt-get install gnupg curl
RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
RUN echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
RUN echo "deb http://security.ubuntu.com/ubuntu focal-security main" | tee /etc/apt/sources.list.d/focal-security.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 871920D1991BC93C
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32
RUN apt update

RUN apt-get install -y libssl1.1
RUN apt-get install -y mongodb-org

WORKDIR /app

COPY src/package*.json ./
RUN npm install
COPY src/. .

RUN mkdir keys

RUN mkdir agent
COPY agent/agent ./agent/agent

COPY src/. .

# Expose the port the app runs on
EXPOSE 3000

# Define the command to run the app
CMD ["bash", "init.sh"]
