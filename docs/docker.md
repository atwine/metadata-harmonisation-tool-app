# Running via Docker Compose

This is the packaged way to run the app for a non-technical end user, without installing
Python, Node, or Ollama separately. Everything runs locally — no data leaves the machine,
and no shared/hosted AI backend is used.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose).
  On Windows this also installs WSL2.
- At least ~8GB free RAM and a few GB of free disk space for the bundled AI models.

## First run

```bash
docker compose up
```

The first run will:
1. Build the `backend` and `frontend` images.
2. Pull the `ollama/ollama` image.
3. Start Ollama, then download the chat model (`llama3.2:3b`) and embedding model
   (`nomic-embed-text`) into a persistent volume — this step is the slow part (several GB).

Once you see `[ollama-entrypoint] models ready — serving.` in the logs, open:

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000

Every run after the first is fast — the models stay cached in the `ollama_data` Docker
volume and aren't re-downloaded.

## Your data

Uploaded studies, mapping results, the audit trail, and the AfPO gap log are stored in
`./harmonisation-data/` next to `docker-compose.yml` — a normal folder on your machine,
not something hidden inside Docker. Back it up by copying it, the same way you'd back up
any other folder.

This is a deliberate choice: `docker compose down -v` (which deletes Docker-managed
volumes) does **not** touch this folder, because it isn't a Docker volume. Your work is
safe even if someone runs that command to "reset" the app.

The only thing that *does* live in a Docker-managed volume is the Ollama model cache
(`ollama_data`) — losing that just means re-downloading the models on the next `up`, not
losing any of your work.

## Stopping / restarting

```bash
docker compose down     # stops containers, keeps all data and the model cache
docker compose up       # starts again, fast (models already cached)
```

Avoid `docker compose down -v` unless you specifically want to wipe the Ollama model
cache too (your study/mapping data in `./harmonisation-data/` is unaffected either way).

## Using a different AI provider

The AI Configuration sidebar in the app works the same as in a manual install — you can
still switch to vLLM, OpenAI, Anthropic, or Azure OpenAI per chat/embedding slot if you'd
rather not use the bundled Ollama.

## Troubleshooting

- **"AI not configured" / connection fails right after `up`**: the model pull can take
  several minutes on first run. Check `docker compose logs ollama` — wait for
  "models ready — serving."
- **Permission errors writing to `./harmonisation-data/` on Linux**: Docker auto-creates
  bind-mount folders as `root`. If you hit this, either run
  `sudo chown -R $(id -u):$(id -g) ./harmonisation-data` once, or open an issue — this
  hasn't been hit in testing yet and may need a container-side fix.
