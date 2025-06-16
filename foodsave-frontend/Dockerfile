# Use official Node.js image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./

# Install dependencies (prefer ci if lockfile exists)
RUN if [ -f package-lock.json ]; then npm ci; \
    else npm install; fi

# Copy source code
COPY . .

# Build the Next.js application
RUN npm run build || true

# Expose port 3000
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
