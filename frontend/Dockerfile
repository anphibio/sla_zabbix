FROM node:22.22.3-alpine3.24

WORKDIR /app/frontend

COPY frontend /app/frontend

EXPOSE 5173

CMD ["sh", "-lc", "if [ ! -f package.json ]; then echo 'frontend/package.json is not present yet, so the frontend container remains a scaffold until the package manifest is added.'; exit 1; fi; npm install && npm run dev -- --host 0.0.0.0 --port 5173"]
