# ToDo App — Node.js and MongoDB

A small server-rendered ToDo application used in the Kubernetes 06 microservices lab. The web tier is an Express application and the data tier is MongoDB.

## Run locally with Docker Compose

From this directory:

```bash
docker compose -f compose/docker-compose.yaml up --build -d
docker compose -f compose/docker-compose.yaml ps
docker compose -f compose/docker-compose.yaml logs -f web
```

Open http://localhost:3000.

Stop the containers:

```bash
docker compose -f compose/docker-compose.yaml down
```

The named volume `mongo-data` preserves database data. To delete the volume and all stored ToDo data as well:

```bash
docker compose -f compose/docker-compose.yaml down -v
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PORT` | HTTP listen port | `3000` |
| `DBHOST` | MongoDB connection URI | `mongodb://db:27017/express-todo` |

For Docker Compose, the hostname `db` is the database service name. In Kubernetes, the manifest sets `DBHOST` to `mongodb://db-service:27017/express-todo`.

## Build an image for Kubernetes

Build from the `todo-app` directory and push to a registry your cluster can access:

```bash
docker build -t YOUR_REGISTRY/todo-app:1.0 .
docker push YOUR_REGISTRY/todo-app:1.0
```

Update the image reference in `kubernetes/web-deployment.yaml` before applying the Kubernetes manifests.

## Project structure

```text
app/
├── app.js
├── db.js
├── utils.js
├── routes/
│   └── index.js
├── views/
│   ├── edit.ejs
│   ├── index.ejs
│   └── layout.ejs
└── public/
    └── stylesheets/
        └── screen.css
```

## Notes

- `node_modules` is intentionally excluded. Dependencies are installed from `app/package.json` during the image build.
- Do not commit a real `.env` file or credentials.
- This is a learning application, not a production-ready task manager. Add authentication, authorization, CSRF protection, rate limiting, and operational monitoring before production use.
