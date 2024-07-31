# Use the official Node.js image.
FROM node:latest

# Create and change to the app directory.
WORKDIR /usr/web

COPY . .

# Install app dependencies.
RUN npm install

# Expose the port the app runs on.
EXPOSE 5000

# Run the app.
CMD ["node", "index.js"]
