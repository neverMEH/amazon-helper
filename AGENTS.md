# Repository Guidelines

## Project Structure & Module Organization
The FastAPI backend lives in `amc_manager/`, with request handlers under `api/`, domain services in `services/`, and shared config and utilities in `config/` and `core/`. React code sits in `frontend/src/`, where `components/` holds UI building blocks and `services/` wraps API calls. Database assets are tracked in `database/` and `migrations/`, while automation scripts reside in `scripts/`. Backend and integration tests are grouped in `tests/` following domain-oriented subfolders.

## Build, Test, and Development Commands
Run `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` to set up backend dependencies. Start both services via `./start_services.sh`, or run the API alone with `python main_supabase.py`. Frontend workflows use `npm install` then `npm run dev` inside `frontend/`. Use `npm run build` to generate the production bundle and `npm run preview` to smoke-test it locally.

## Coding Style & Naming Conventions
Format Python code with `black` (88-character lines) and verify lint results with `flake8`; backend modules and functions follow `snake_case`, while FastAPI routers use `router_name.py` files. TypeScript modules use PascalCase for components, camelCase for hooks and utilities, and Tailwind utility classes for styling. Run `npm run lint` before sending UI changes to keep ESLint and TypeScript happy.

## Testing Guidelines
Execute backend tests with `pytest` from the repo root; target a failing area quickly using `pytest tests/services -k scheduler`. Frontend unit tests live alongside source in `frontend/src` and run via `npm test` or `npm run test:coverage`. When adding new features, back API changes with `tests/api/test_<feature>.py`, and prefer Vitest component specs in `frontend/src/__tests__/` or colocated `*.test.tsx` files. Update fixtures under `tests/integration/` if API contracts change.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits (e.g., `fix: handle empty schedule window`), so choose `feat`, `fix`, `docs`, or `refactor` prefixes that match the change. Keep pull requests focused, include a short summary of user impact, link Supabase tickets or GitHub issues, and attach screenshots or terminal output for UI or workflow updates. Mention any required config changes (env vars, migrations) and tick off relevant tasks in the PR checklist before requesting review.

## Environment & Configuration
Copy `test_env/.env.example` or project-level examples into `.env` for Supabase credentials, then update secrets through your local `.env` without committing them. The backend respects `SUPABASE_*` and rate-limit settings, while local development expects PostgreSQL credentials via Railway or Supabase CLI. Restart `start_services.sh` after changing environment variables to reload tokens and background schedulers.
