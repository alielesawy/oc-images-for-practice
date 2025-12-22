# Base Image
FROM registry.access.redhat.com/ubi8/nodejs-16

# Work Directory
WORKDIR /opt/app-root/src

# Install dependencies first (for caching)
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Expose port (OpenShift uses 8080 by default for non-root)
EXPOSE 8080

# Start command
CMD ["npm", "start"]
