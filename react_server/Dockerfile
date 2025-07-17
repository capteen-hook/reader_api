# Use the official Node.js image from the Docker Hub
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json (or yarn.lock) into the container
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app files into the container
COPY . .

# Build the Next.js app
RUN npm run build

# Expose the port the app will run on (default is 3000 for Next.js)
EXPOSE 3000

# Start the app in production mode
CMD ["npm", "start"]
