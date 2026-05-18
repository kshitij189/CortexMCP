# CortexMCP Production Deployment Guide

This guide describes how to deploy the CortexMCP stack in production. It details host recommendations for each tier of the stack, outlines the configuration files prepared for this purpose, and provides a step-by-step walkthrough for deploying the unified stack using Docker Compose.

---

## 🏛️ Production Recommendations by Stack Tier

For a production environment, it is highly recommended to segregate the services and leverage **managed cloud services** instead of running everything inside simple containers on a single host. This ensures scalability, zero downtime, auto-backup, and fault isolation.

### 1. Frontend (Vite React SPA)
Since the frontend is a purely static Single Page Application (SPA), it should be served from a CDN rather than a running Node server.
* **Vercel (Recommended - Free Tier Available):** Extreme performance, global edge CDN, and automatic Git-integrated deployments.
* **Netlify / Cloudflare Pages:** Highly robust alternatives offering free global CDNs and custom headers/routing.
* **Nginx in Docker:** If self-hosting is required, serve it using the prepared `frontend/Dockerfile.prod` and `frontend/nginx.conf` behind Nginx.

### 2. Backend API (FastAPI Gateway)
Needs a containerized running application environment.
* **Render Web Services:** Fast, simple, automatically handles TLS/SSL certificates, and integrates directly with Git.
* **Railway:** Highly popular developer platform with automatic Dockerfile builds and instant deployments.
* **Google Cloud Run:** Serverless container deployment that automatically scales to zero when idle, minimizing costs.
* **AWS ECS / Fargate:** Enterprise-grade container orchestrator with elastic load balancing.

### 3. Background Task Runner (Celery Worker)
Needs to be hosted in an environment that allows long-running, continuous background processes (not serverless scale-to-zero).
* **Render Background Worker:** Dedicated server type for background processes; connects securely to Redis and PostgreSQL.
* **Railway:** You can spin up a separate Railway service executing `celery -A app.workers.celery_app worker --loglevel=info`.
* **AWS ECS / Fargate:** Runs as a task definition inside your ECS cluster without an exposed public port.

### 4. Relational Database (PostgreSQL)
**Never** host stateful databases inside ephemeral containers in production without persistent block storage.
* **Neon.tech (Recommended):** High-performance serverless Postgres with instant branching, auto-scaling, and generous free tier.
* **Supabase:** Fully managed Postgres database with connection pooling enabled.
* **AWS RDS (PostgreSQL):** Enterprise standard with automated snapshots, multi-AZ high availability, and failover.
* **Render Managed PostgreSQL:** Simple, instant database addition that is co-located with Render web services.

### 5. Message Broker & Event Cache (Redis)
Used for queue brokerage and Server-Sent Events (SSE) log broadcasting.
* **Upstash Redis (Recommended):** Serverless Redis billed by request volume. It handles connection pooling gracefully and has a free tier.
* **Redis Enterprise / Render Redis / Railway Redis:** Standard managed Redis instances with guaranteed uptimes.

### 6. Vector Database (ChromaDB)
Used to store transient page chunks for semantic deduplication.
* **SQLite Volume Mount:** When running inside Docker, ensure a persistent volume (`chroma_prod_data`) is attached to both the API and Celery Worker containers.
* **Chroma standalone (Hosted Cloud/AWS):** You can spin up a standalone Chroma server container on AWS ECS/EC2 and point `CHROMA_SERVER_HOST` to it.

---

## 🛠️ Prepared Production Configurations

We have added three files to the repository to prepare the project for deployment:

1. **[frontend/nginx.conf](file:///c:/Users/rog/Downloads/CortexMCP/frontend/nginx.conf):** Production Nginx configuration that properly serves the Vite static build files and supports **React Router SPA fallbacks** (preventing `404 Not Found` when refreshing deep URLs like `/report/:id`).
2. **[frontend/Dockerfile.prod](file:///c:/Users/rog/Downloads/CortexMCP/frontend/Dockerfile.prod):** A multi-stage Docker build:
   - *Stage 1 (Node):* Installs production dependencies and compiles static assets (`npm run build`).
   - *Stage 2 (Nginx):* Installs Nginx and copies static build files into the Nginx serving root, resulting in a lightweight (~20MB) secure image.
3. **[docker-compose.prod.yml](file:///c:/Users/rog/Downloads/CortexMCP/docker-compose.prod.yml):** A dedicated production-grade compose file:
   - Removes raw volume mappings (avoiding local NTFS watch conflicts).
   - Disables hot-reload flags on FastAPI (`--reload` is removed to save CPU).
   - Binds the frontend Nginx to standard HTTP Port `80`.

---

## 🚀 Step-by-Step Deployment Walkthrough

Here are the step-by-step instructions to deploy the entire stack using Docker Compose on a single Virtual Private Server (VPS like DigitalOcean, Linode, AWS EC2, or Hetzner).

### Step 1: Provision your VPS
Create a Linux virtual machine (Ubuntu 22.04 LTS recommended) and ensure that ports **`80`** (HTTP), **`443`** (HTTPS), and **`8001`** (FastAPI) are open in your network firewall.

### Step 2: Install Docker and Docker Compose
Log into your server via SSH and run:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

### Step 3: Clone and Setup Configuration
1. Clone the repository on the server:
   ```bash
   git clone https://github.com/kshitij189/CortexMCP.git
   cd CortexMCP
   ```
2. Create your production environment file `.env` in the root folder:
   ```env
   # Database Credentials
   POSTGRES_USER=cortex_prod_user
   POSTGRES_PASSWORD=secure_production_password_here
   POSTGRES_DB=cortexmcp_prod

   # External LLM & Search API Keys
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

### Step 4: Run Alembic Database Migrations
Before spinning up the containers, run your database migrations to create all required schemas (including the self-referencing temporal parent keys):
```bash
# Start Postgres and Redis first
docker compose -f docker-compose.prod.yml up -d postgres redis

# Run Alembic migration inside a temporary container
docker compose -f docker-compose.prod.yml run --entrypoint "alembic upgrade head" api
```

### Step 5: Launch the Production Stack
Spin up the rest of the services in background daemon mode:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
This builds your production Nginx frontend image, downloads PyTorch CPU into the API/Celery services, and spins up all five containers securely.

### Step 6: Verify Health
Run `docker compose -f docker-compose.prod.yml ps` to verify all five containers are in the `running` state:
* **cortexmcp-frontend-prod:** listening on port `80`
* **cortexmcp-api-prod:** listening on port `8001`
* **cortexmcp-celery-prod:** background processing
* **cortexmcp-postgres-prod:** port `5433`
* **cortexmcp-redis-prod:** port `6380`

---

## 🔒 Post-Deployment Security Check
1. **Enable SSL/TLS (HTTPS):** Set up **Nginx** or **Caddy** on the host server as a reverse proxy to route traffic from Port `443` to the frontend (port `80`) and backend (port `8001`), and secure it with Let's Encrypt certificates.
2. **Restrict Port Access:** Close ports `5433` (Postgres) and `6380` (Redis) to the public internet using `ufw` or your cloud security group, ensuring they can only be reached internally by your containers.
