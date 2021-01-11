FROM node:12

# Set working directory
WORKDIR /app

# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY package*.json ./

## Install only the packages defined in the package-lock.json (faster than the normal npm install)
RUN npm install yarn --no-package-lock && yarn

# Copy the contents of the project to the image
COPY . .

EXPOSE 3000

CMD ["npm", "start"]