# Docker build & publish guide

This file explains how to build and push a Docker image for this project, and how to run it locally or use the published image on a host.

1) Local build & run (quick test)

```bash
# from the project root (where Dockerfile is)
docker build -t recruitment_system:latest .
docker run --rm -p 8000:8000 recruitment_system:latest
```

Open http://localhost:8000 and the API docs at /docs.

2) Publish to Docker Hub using GitHub Actions (automated)

- Create a Docker Hub repository named `recruitment_system` (or any name you prefer).
- In your GitHub repo settings, add two Secrets:
  - `DOCKERHUB_USERNAME` — your Docker Hub username
  - `DOCKERHUB_TOKEN` — a Docker Hub access token (create in Docker Hub Settings > Security)

When you push to `main`, the workflow `.github/workflows/docker-publish.yml` will build the image and push it as `DOCKERHUB_USERNAME/recruitment_system:latest`.

3) Deploying the image

- Use any host that can run Docker images (Render, Fly.io, DigitalOcean App Platform, a VPS).
- Example: on a server with Docker installed:

```bash
docker pull yourusername/recruitment_system:latest
docker run -d --name recruitment_system -p 8000:8000 yourusername/recruitment_system:latest
```

4) Notes
- The GitHub Action requires the `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets. I cannot create them for you — you must add them in the GitHub repository settings.
- If you want me to set up auto-deploy to Render or Fly.io, I can add a second workflow (it will require their API key as a GitHub secret).
