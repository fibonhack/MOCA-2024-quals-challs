# Use the official Node.js image.
FROM node:latest

# Create and change to the app directory.
WORKDIR /usr/src/app

# Copy package.json and package-lock.json.
# Install necessary dependencies for Puppeteer.
# See: https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    --no-install-recommends \
    && apt-get install -y \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgconf-2-4 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libgbm-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY package*.json ./

# Install app dependencies.
RUN npm install

# Bundle app source code.
COPY . .


# Expose the port the app runs on.
EXPOSE 3000

# Run the app.
CMD ["node", "app.js"]
