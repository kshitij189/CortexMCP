FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

# Expose Vite's default port
EXPOSE 5173

# Start Vite server, binding to all network interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
