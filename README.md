# Rosetta

<p align="center">
  <a href="https://github.com/ChuyuChoyeon/Rosetta">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 220'><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0%25' stop-color='%23FF5D01'/><stop offset='50%25' stop-color='%237C3AED'/><stop offset='100%25' stop-color='%23009485'/></linearGradient></defs><rect width='1200' height='220' rx='24' fill='%230b1020'/><path d='M80 40h1040l-60 140H140Z' fill='url(%23g)' opacity='0.12'/><text x='80' y='110' fill='white' font-family='Inter,system-ui,sans-serif' font-size='56' font-weight='800' letter-spacing='-1'>Rosetta</text><text x='80' y='158' fill='%239db0d0' font-family='Inter,system-ui,sans-serif' font-size='22' font-weight='500'>FastAPI &amp;bull; Astro 7 &amp;bull; Svelte 5 &amp;bull; SQLAlchemy Async</text><g transform='translate(980 68)'><rect width='152' height='84' rx='18' fill='none' stroke='%23ffffff22'/><g transform='translate(18 18)' fill='%23ffffffcc' font-family='ui-monospace,monospace' font-size='12'><rect width='16' height='16' rx='4' fill='%23FF5D01'/><rect x='22' width='16' height='16' rx='4' fill='%23009485'/><rect x='44' width='16' height='16' rx='4' fill='%237C3AED'/><text y='44' fill='%239db0d0'>%24 uv run uvicorn</text><text y='60' fill='%239db0d0'>%24 pnpm dev</text></g></g></svg>"/>
      <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 220'><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0%25' stop-color='%23FF5D01'/><stop offset='50%25' stop-color='%237C3AED'/><stop offset='100%25' stop-color='%23009485'/></linearGradient></defs><rect width='1200' height='220' rx='24' fill='%23f7f8fb'/><path d='M80 40h1040l-60 140H140Z' fill='url(%23g)' opacity='0.10'/><text x='80' y='110' fill='%230b1020' font-family='Inter,system-ui,sans-serif' font-size='56' font-weight='800' letter-spacing='-1'>Rosetta</text><text x='80' y='158' fill='%23475569' font-family='Inter,system-ui,sans-serif' font-size='22' font-weight='500'>FastAPI &amp;bull; Astro 7 &amp;bull; Svelte 5 &amp;bull; SQLAlchemy Async</text><g transform='translate(980 68)'><rect width='152' height='84' rx='18' fill='white' stroke='%2300000014'/><g transform='translate(18 18)' font-family='ui-monospace,monospace' font-size='12'><rect width='16' height='16' rx='4' fill='%23FF5D01'/><rect x='22' width='16' height='16' rx='4' fill='%23009485'/><rect x='44' width='16' height='16' rx='4' fill='%237C3AED'/><text y='44' fill='%23475569'>%24 uv run uvicorn</text><text y='60' fill='%23475569'>%24 pnpm dev</text></g></g></svg>" alt="Rosetta Banner"/>
    </picture>
  </a>
</p>

<p align="center">
  Full-stack blog CMS. FastAPI async backend, Astro 7 + Svelte 5 frontend.<br/>
  Async-first, type-safe end-to-end, batteries included.
</p>

<p align="center">
  <a href="https://github.com/ChuyuChoyeon/Rosetta/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/build-passing-%23009485?style=flat-square&logo=githubactions&logoColor=white" alt="Build"/></a>
  <a href="https://github.com/ChuyuChoyeon/Rosetta/blob/main/LICENSE"><img src="https://img.shields.io/github/license/ChuyuChoyeon/Rosetta?style=flat-square&color=%237C3AED" alt="License"/></a>
  <a href="https://github.com/ChuyuChoyeon/Rosetta"><img src="https://img.shields.io/badge/python-3.12%2B-%233776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://github.com/ChuyuChoyeon/Rosetta"><img src="https://img.shields.io/badge/typescript-6.0-%233178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/></a>
  <a href="https://github.com/ChuyuChoyeon/Rosetta"><img src="https://img.shields.io/badge/astro-7-%23FF5D01?style=flat-square&logo=astro&logoColor=white" alt="Astro"/></a>
  <a href="https://github.com/ChuyuChoyeon/Rosetta"><img src="https://img.shields.io/badge/svelte-5-%23FF3E00?style=flat-square&logo=svelte&logoColor=white" alt="Svelte"/></a>
</p>

---

## Architecture

```
                                ┌─────────────────────────────┐
  Browser / App  ─────────────▶ │  Astro 7 Static + SSR MIX  │
           ▲                    │  (Tailwind v4 / Svelte 5)  │
           │                    └──────────────┬──────────────┘
           │ HTTPS / WSS                       │ /api, /media, /oauth
           │                    ┌──────────────▼──────────────┐
           └────────────────────│  FastAPI + SQLAlchemy Async │
               reverse-proxy    │  JWT / CSRF / Rate-limit    │
                                └──────┬─────────────┬─────────┘
                                       │             │
                                ┌──────▼──┐   ┌──────▼───────┐
                                │   DB    │   │    Cache     │
                                │ PG / SL │   │ Redis / Mem  │
                                └─────────┘   └──────────────┘
```

## Key Features

| | | |
|---|---|---|
| **User System**<br/>Multi-role RBAC, JWT, QQ / GitHub avatars, password policy, ban / soft-delete, bulk admin ops | **Comment System**<br/>Anonymous + Authenticated, nested replies, sensitivity analysis, original-storage XSS, reactions, moderation batch API | **Navigation Tree**<br/>Unlimited depth hierarchy, drag &amp; drop reorder, link / category / tag / archive / page node types, icon + target + rel |
| **Post Editor**<br/>Split-pane Markdown + live preview, chips, cover picker, series, scheduled, password/token encrypt, SEO, revisions + recycle bin | **Presentational**<br/>Astro Islands, Tailwind v4, dark/light/system, Sakura &amp; canvas effects, Live2D + Spine, Pagefind offline search | **Pages**<br/>Gallery (auto avif/webp + LQIP), Bangumi, Timeline dynamics, Guestbook, Category/Tag archive, Friends, Sponsor |
| **Admin Console**<br/>`/admin` dashboard, stat cards, CRUD for posts/categories/tags/nav/albums/dynamics/announcements/banners/friends/settings | **i18n**<br/>6 built-in locales, type-safe `i18nKey` with autocompletion | **Security**<br/>CSRF double-submit, HSTS/CSP/XFO headers, rate-limited auth, bcrypt + salt, ORM parameterized end-to-end |
| **Deployment**<br/>`docker compose up -d` (PG + Redis + Backend + Nginx), Cloudflare Workers, Vercel button | **Tests**<br/>Backend 326 pytest cases passed; frontend biome + astro check + build all green | **OpenAPI**<br/>Auto Swagger UI at `/docs`, ReDoc at `/redoc`, health check at `/health` |

## Quick Start

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | [python.org](https://www.python.org) |
| uv | latest | [docs.astral.sh](https://docs.astral.sh/uv/getting-started/installation/) |
| Node.js | 22+ | [nodejs.org](https://nodejs.org) |
| pnpm | 10+ | `corepack enable && corepack prepare pnpm@10 --activate` |
| SQLite | bundled | (zero-config default) |

### Backend

```bash
git clone https://github.com/ChuyuChoyeon/Rosetta.git
cd Rosetta
uv sync
cp .env.example .env
uv run python -m backend.migrations upgrade
uv run uvicorn backend.main:app --reload --port 8000
```

Docs:
- Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health: <http://localhost:8000/health>

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open <http://localhost:4321>. The OOBE wizard guides you through DB config, admin creation, and seed content.

---

## Docker (recommended for production)

```bash
cp .env.example .env   # tweak SECRET_KEY / DB_PASSWORD / CORS_ORIGINS
docker compose up -d
```

| Service | URL / Address |
|---|---|
| Frontend (Nginx) | <http://localhost> |
| Backend API | <http://localhost:8000> |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

---

## Project Layout

```
rosetta/
├── backend/                 FastAPI application
│   ├── api/                 routes by domain
│   ├── core/                config / db / auth / cache / i18n / security
│   ├── middleware/          performance / logging / HSTS
│   ├── migrations/          Alembic revisions (18+ versions)
│   ├── models/              SQLAlchemy ORM
│   ├── repositories/        data-access layer
│   ├── schemas/             Pydantic request / response
│   ├── services/            business logic
│   ├── docs/                API reference + error codes
│   └── main.py              entry
├── frontend/                Astro 7 + Svelte 5
│   ├── src/
│   │   ├── api/             typed TS client
│   │   ├── components/      Astro + Svelte (full admin/*)
│   │   ├── config/          site configuration modules
│   │   ├── content/         Markdown / MDX collections
│   │   ├── i18n/            translations + i18nKey types
│   │   ├── layouts/
│   │   ├── pages/           file-system routing incl. /admin/*
│   │   └── plugins/         remark / rehype pipeline
│   ├── public/              static assets (favicon, fonts, models)
│   ├── scripts/             build-time scripts (LQIP, font-subset)
│   └── astro.config.mjs
├── docker/                  nginx.conf + entrypoint
├── Dockerfile               multi-stage build
├── docker-compose.yml
├── .env.example
└── DEPLOY.md
```

---

## Testing

```bash
# Backend — 326 cases passing
uv run pytest -q

# Frontend — all green
cd frontend
pnpm biome check ./src
pnpm astro check
CF_WORKERS=1 pnpm build
```

## Default admin (dev-mode OOBE skip)

| | |
|---|---|
| Username | `admin` |
| Password | `Admin123456` |

**Change it immediately in production.**

---

## Documentation

- [Deployment Guide](DEPLOY.md) — systemd / Nginx / PostgreSQL full walkthrough
- [Backend API Reference](backend/docs/api_reference.md)
- [Error Codes](backend/docs/error_codes.md)
- [Contributing](frontend/CONTRIBUTING.md)

## License

MIT
