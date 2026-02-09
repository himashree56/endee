# Deployment Guide: Hybrid Cloud (Recommended)

This guide outlines the steps to deploy the AI Research Assistant using a hybrid architecture for maximum performance, scalability, and cost-efficiency.

<<<<<<< HEAD
=======
## Architecture
This guide outlines the steps to deploy the AI Research Assistant using a hybrid architecture for maximum performance, scalability, and cost-efficiency.

>>>>>>> 8d12097 (updated again)
## 🏗️ Architecture
```mermaid
graph TD
    User[User Browser] -->|Visit URL| Vercel[Frontend (Vercel)]
    Vercel -->|API Calls (fetch)| API[Python API (Render)]
    API -->|Vectors| DB[Endee DB (Render)]
```

---

## Part 1: Deploy Endee DB (Render)
The database serves as the high-performance vector heart of the system.

<<<<<<< HEAD
1.  Create a new **Web Service** on [Render](https://render.com).
2.  Connect your repository and set the **Root Directory** to the base project folder (where `CMakeLists.txt` and the top-level `Dockerfile` reside).
3.  **Runtime**: `Docker`.
4.  **Plan**: `Free` (or Starter for persistent disk).
5.  **Environment Variables**:
    - `PORT`: `8080` (Internal port for Endee).
6.  Once deployed, copy the **Service URL** (e.g., `https://endee-db.onrender.com`).
=======
1.  Deploy the **Root Directory** of the repository to Render as a "Web Service".
2.  **Name**: `endee-db`.
3.  **Docker**: Yes.
4.  **Environment Variables**:
    - `PORT`: `8080` (Internal port for Endee).
5.  Once deployed, copy the **Service URL** (e.g., `https://endee-db.onrender.com`).
>>>>>>> 8d12097 (updated again)

---

## Part 2: Deploy Python API (Render)
The API handles document processing, summarization, and retrieval logic.

1.  Create another **Web Service** on Render.
2.  **Name**: `pdf-search-api`.
3.  **Root Directory**: `pdf_search`.
4.  **Runtime**: `Docker`.
5.  **Environment Variables**:
    - `ENDEE_URL`: Paste the Service URL from Part 1.
    - `OPENROUTER_API_KEY`: Your OpenRouter key.
    - `PORT`: `8000`.
6.  Copy the **API URL** (e.g., `https://pdf-search-api.onrender.com`).

---

## Part 3: Deploy Frontend (Vercel)
Vercel provides a global CDN for a blazing-fast user interface.

1.  Connect your repo to [Vercel](https://vercel.com).
2.  **Framework Preset**: `Vite`.
3.  **Root Directory**: `pdf_search/frontend`.
4.  **Environment Variables**:
    - `VITE_API_URL`: Paste the **API URL** from Part 2.
5.  **Deploy**.

---

## 🔧 Environment Variable Checklist

| Key | Value | Location |
| :--- | :--- | :--- |
| `ENDEE_URL` | Endee Service URL | Render (API) |
| `OPENROUTER_API_KEY` | your_key_here | Render (API) |
| `VITE_API_URL` | Python API URL | Vercel (Frontend) |

---

## Why this is better?
<<<<<<< HEAD
- **Blazing Fast UI**: Vercel's Edge Network serves the React app with minimal latency.
- **Independent Scaling**: Scale the database and the compute-heavy API separately.
- **Improved Reliability**: A crash in the API layer won't take down the entire user interface.
=======
- **Faster UI**: Vercel is much faster at serving static assets than Python/Uvicorn.
- **Cheaper**: You can often fit the API + DB on Render Free Tier separately.
- **Separation**: Frontend crashes don't kill the API, and vice-versa.
>>>>>>> 8d12097 (updated again)

> [!TIP]
> **Pro Tip**: Use Render's "Blueprints" (`render.yaml`) to automate the backend deployment.
