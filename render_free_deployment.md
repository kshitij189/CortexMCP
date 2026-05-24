# 🚀 CortexMCP: Completely Free Cloud Deployment Guide

This guide describes how to deploy the entire **CortexMCP** research engine completely for **FREE** using serverless and developer-tier cloud services. 

Since you execute your project locally using Docker, **you do not need Node.js or Python installed locally.** The cloud platforms will compile and deploy your code directly from your GitHub repository.

---

## 🏛️ Free Tier Tech Stack Mapping

To achieve a 100% free production deployment, we map the services as follows:

1. **Frontend (Vite React):** **Render Static Site** *(100% Free - unlimited bandwidth)*
2. **API & Background Worker (FastAPI & Celery):** **Render Web Service** *(Free Tier - runs both API & Celery inside a single container using a startup script to bypass background worker charges!)*
3. **Database (PostgreSQL 16):** **Neon.tech** *(Free Tier - 0.5 GiB storage, serverless autoscaling)*
4. **Queue Broker & Cache (Redis):** **Upstash Redis** *(Free Tier - up to 10,000 commands/day, serverless)*

---

## 🛠️ Files Added to Support Free Deployment

The following files have been added to your codebase to support hosting:
1. **[`backend/start.sh`](file:///c:/Users/rog/Downloads/CortexMCP/backend/start.sh):** A startup shell script that automatically runs Alembic database migrations, boots the Celery background worker, and launches the FastAPI gateway inside a single container.
2. **[`backend/Dockerfile.render`](file:///c:/Users/rog/Downloads/CortexMCP/backend/Dockerfile.render):** A custom Dockerfile optimized to build the backend image on Render and run `start.sh`.

---

## 📋 Pre-requisites
1. Push your latest code changes to your GitHub repository:
   ```bash
   git add .
   git commit -m "chore: prepare codebase for free tier Render, Neon, and Upstash deployment"
   git push origin main
   ```

---

## 🚀 Step-by-Step Free Deployment Blueprint

### Step 1: Spin Up a Free Redis Database on Upstash
1. Go to [Upstash Console](https://console.upstash.com/) and register a free account.
2. Click **Create Database**.
3. Set the name to `cortexmcp-redis` and select your nearest region.
4. Keep the **Free Tier** selected (10k requests/day).
5. Scroll down to the **URIs** section and copy the **Redis URL** (starts with `rediss://default:...`).

---

### Step 2: Spin Up a Free PostgreSQL Database on Neon
1. Go to [Neon.tech](https://neon.tech/) and register a free account.
2. Click **Create Project**.
3. Name your project `CortexMCP` and choose your region.
4. Copy the **Connection String** provided on your dashboard. It will look like this:
   ```
   postgresql://neondb_owner:PASSWORD@ep-xyz-123.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

---

### Step 3: Spin Up FastAPI & Celery as a Render Web Service
Since Render only allows one free web service per account and charges for "Background Workers", we run **both** the FastAPI web server and Celery background worker inside a single Render Web Service container using our custom startup script!

1. Go to [Render Dashboard](https://dashboard.render.com/) and sign in.
2. Click **New +** > **Web Service**.
3. Connect your GitHub repository.
4. Configure the Web Service:
   * **Name:** `cortexmcp-backend`
   * **Instance Type:** **Free**
   * **Region:** Same region as Neon / Upstash if possible
   * **Runtime:** `Docker`
   * **Root Directory:** `backend` *(Crucial: pointing to the backend subfolder)*
   * **Docker Path:** `Dockerfile.render` *(Crucial: relative path inside the backend folder)*
   * **Docker Command:** *(Leave blank - it will default to `CMD` in Dockerfile.render)*
5. Click **Advanced** and add the following **Environment Variables**:
   * `DATABASE_URL`: *[Insert the PostgreSQL connection string from Neon]*
   * `REDIS_URL`: *[Insert the Redis URL from Upstash]*
   * `TAVILY_API_KEY`: *[Your Tavily Search Key]*
   * `GEMINI_API_KEY`: *[Your Gemini LLM Key]*
   * `GROQ_API_KEY`: *[Your Groq Fallback Key]*
   * `PORT`: `10000` *(Render default port)*
6. Click **Create Web Service**. Render will build and deploy the Docker image (pre-installing PyTorch and all dependencies), execute your database migrations, and boot both the API and worker. 
7. Copy your backend web service's live URL (e.g., `https://cortexmcp-backend.onrender.com`).

---

### Step 4: Spin Up the React Frontend as a Render Static Site
Render Static Sites are 100% free and served over a high-speed CDN. The build process happens fully on Render.

1. Go to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** > **Static Site**.
3. Connect your GitHub repository.
4. Configure the Static Site:
   * **Name:** `cortexmcp-frontend`
   * **Root Directory:** `frontend` *(Crucial: pointing to the frontend subfolder)*
   * **Build Command:** `npm run build`
   * **Publish Directory:** `dist`
5. Click **Advanced** and add the following **Environment Variable**:
   * **`VITE_API_URL`**: `https://cortexmcp-backend.onrender.com/api` *(Make sure to replace this with your actual Render backend URL, appending `/api` at the end!)*
6. Click **Create Static Site**.
7. **Configure Redirects/Rewrites (Crucial for React Router/SPA support):**
   * After the static site is created, go to the **Redirects/Rewrites** tab in the service's left sidebar.
   * Click **Add Rule** and enter:
     * **Source:** `/*`
     * **Destination:** `/index.html`
     * **Action:** `Rewrite`
   * Click **Save**. *(This ensures that refreshing pages like `/dashboard` or `/report/:id` loads the React app correctly instead of returning a 404 Not Found error).*
8. Once finished, visit your live static site URL (e.g., `https://cortexmcp-frontend.onrender.com`) to register, log in, select personas, and execute async research updates completely in the cloud!

---

## ⚠️ Notes on Render's Free Tier Behavior
* **Cold Starts:** Free Web Services on Render automatically spin down to save resources if they receive no HTTP traffic for 15 minutes. When you open the frontend, the backend might take **50–90 seconds** to wake up for the first request.
* **Database Sleep:** Neon database compute instances also spin down after 5 minutes of inactivity, waking up instantly (in ~2 seconds) on any query.
