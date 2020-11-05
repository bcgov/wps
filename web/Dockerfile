FROM node:10

# Set working directory
WORKDIR /app

# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY package*.json ./

# Install all the dependencies to run the application in development mode
RUN npm set progress=false && npm ci --no-cache

# Copy the contents of the project to the image
COPY . .

EXPOSE 3000

CMD ["npm", "start"]