# 🚀 CortexMCP: Completely Free Cloud Deployment Guide

This guide describes how to deploy the entire **CortexMCP** research engine completely for **FREE** using serverless and developer-tier cloud services. 

Since you execute your project locally using Docker, **you do not need Node.js or Python installed locally.** The cloud platforms will compile and deploy your code directly from your GitHub repository.

---

## 🏛️ Free Tier Tech Stack Mapping

To achieve a 100% free production deployment, we map the services as follows:

1. **Frontend (Vite React):** **Render Static Site** *(100% Free - unlimited bandwidth)*
2. **API & Background Worker (FastAPI & Celery):** **Render Web Service** *(Free Tier - runs both API & Celery inside a single container using a startup script to bypass background worker charges!)*
3. **Database (PostgreSQL 16):** **Neon.tech** *(Free Tier - 0.5 GiB storage, serverless autoscaling)*
4. **Queue Broker & Cache (Redis):** **Embedded in the backend container** *(no external service, no command quota)*

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

### Step 1: Redis — Nothing to Set Up

Redis runs **inside the backend container** alongside the API and the Celery worker,
so there is no Redis service to create and no `REDIS_URL` to configure. `start.sh`
boots `redis-server` on `127.0.0.1:6379` before starting anything that needs it.

Persistence is deliberately off. Everything durable — job status, scraped sources,
generated reports — lives in Postgres; Redis only holds the in-flight task queue and
the progress pub/sub channel, so losing it on a restart costs nothing but jobs that
were mid-flight.

**Using an external Redis instead (optional).** Set `REDIS_URL` on the web service and
it will be used, but only if it actually answers on boot — if it does not, `start.sh`
logs the reason and falls back to the embedded instance rather than letting every
research request fail. If that external broker is metered, also set
`CELERY_BROKER_POLLING_INTERVAL` to `15` or higher: Celery polls the queue once per
second by default, which is ~86,400 commands a day and on its own exceeds, for
example, Upstash's 10,000/day free allowance.

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
   * **Region:** Same region as Neon if possible
   * **Runtime:** `Docker`
   * **Root Directory:** `backend` *(Crucial: pointing to the backend subfolder)*
   * **Docker Path:** `Dockerfile.render` *(Crucial: relative path inside the backend folder)*
   * **Docker Command:** *(Leave blank - it will default to `CMD` in Dockerfile.render)*
5. Click **Advanced** and add the following **Environment Variables**:
   * `DATABASE_URL`: *[Insert the PostgreSQL connection string from Neon]*
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
