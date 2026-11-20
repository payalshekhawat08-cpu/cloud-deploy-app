# ☁️ Cloud Deployment Practical: Flask Web App on Render

A small web application deployed on a cloud platform to demonstrate core cloud concepts: compute, managed database, networking, access control, secrets management, logging, monitoring and resource quotas.

**Live website:** `PASTE_YOUR_RENDER_URL_HERE`

## Deployment Flow

```
Application Code (GitHub)
        │  auto-deploy on push
        ▼
Cloud Compute (Render Web Service, gunicorn + Flask)
        │  private connection string (env var)
        ▼
Managed Database (Render PostgreSQL)
        │
        ▼
Networking (managed HTTPS, public URL, port binding)
        │
        ▼
Live Web Application
```

## Tech Stack
- **App:** Python, Flask, SQLAlchemy, gunicorn
- **Database:** PostgreSQL (managed, Render); SQLite fallback for local runs
- **Cloud platform:** Render (Blueprint / Infrastructure as Code via `render.yaml`)
- **Source control and CI trigger:** GitHub

## Key Objectives and How They Are Covered

| Objective | Implementation in this project | AWS equivalent |
|---|---|---|
| **Compute services** | Render Web Service runs the Flask app with gunicorn | EC2 / Elastic Beanstalk |
| **Object storage** | Not needed by this app. Static assets are served with the app; user files would go to an S3-compatible bucket | S3 |
| **Managed databases** | Render PostgreSQL, created and wired up through `render.yaml` | RDS |
| **Virtual networking** | Public HTTPS endpoint with managed TLS; the app reaches the database through its connection string; the app binds to the platform-provided `$PORT` | VPC, security groups, load balancer |
| **IAM policies** | GitHub account authorizes Render to read only this repo; database credentials are auto-generated and scoped to this app; the dashboard supports team roles | IAM users, roles, policies |
| **Cloud monitoring** | `/health` endpoint checks app and database; Render runs it as a health check and restarts the service on failure; Render Metrics shows CPU/memory | CloudWatch |
| **Env variables and secrets** | `APP_ENV`, `SECRET_KEY` (auto-generated) and `DATABASE_URL` live only in the platform environment. Nothing is hard-coded and `.env` is git-ignored | Secrets Manager / Parameter Store |
| **Application logging** | Python `logging` writes timestamped logs to stdout; gunicorn access logs enabled; both visible in the Render Logs tab | CloudWatch Logs |
| **Resource quotas** | Free tier limits: 512 MB RAM, shared CPU, service sleeps after about 15 min of inactivity, free PostgreSQL expires after 30 days. Workers kept at 2 to stay within memory | Service quotas, instance sizing |

## Project Structure
```
├── app.py              # Flask app: routes, DB, logging, /health
├── templates/
│   └── index.html      # Frontend page
├── requirements.txt    # Python dependencies
├── render.yaml         # Infrastructure as code (service + database + env vars)
├── .env.example        # Template of required environment variables
├── .gitignore
└── README.md
```

## Run Locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py                   # http://localhost:5000 (uses SQLite)
```

## Deploy to Render
1. Push this repo to GitHub.
2. Sign up at [render.com](https://render.com) with GitHub.
3. Click **New → Blueprint** and select this repository.
4. Render reads `render.yaml`, creates the PostgreSQL database and the web service, and injects the environment variables.
5. Wait for the build to finish, then open the generated `onrender.com` URL.

## Endpoints
| Route | Purpose |
|---|---|
| `/` | Main page: submit and view messages stored in the database |
| `/add` | POST: saves a message |
| `/health` | JSON health status (app, database, uptime) |

## Monitoring and Logs
- **Logs:** Render dashboard → service → *Logs*
- **Metrics:** Render dashboard → service → *Metrics*
- **Health check:** `https://<your-url>/health`

## Screenshots
Add screenshots here (dashboard, environment variables page with values hidden, logs, live site).

## Key Learnings
- Separating configuration from code with environment variables
- Provisioning compute and a managed database as code (Blueprint)
- Using health checks and logs for observability
- Understanding free-tier resource limits and their trade-offs
