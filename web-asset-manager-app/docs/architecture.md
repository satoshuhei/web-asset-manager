# Architecture (Web Asset Manager)

## Stack
- Backend: FastAPI (Python)
- Templates: Jinja2
- Frontend: Vanilla JS + CSS
- Database: SQLite

## Layers
1. **API & Web**: FastAPI routes in app.py serve HTML and JSON.
2. **Services**: Business logic in src/wam/services.py.
3. **Repositories**: Data access in src/wam/repositories.py.
4. **Database**: Schema and seed logic in src/wam/db.py.

## Data Flow
- User action (UI) → FastAPI route → Service → Repository → SQLite
- Configuration card positions are saved via /api/configs/{id}/position.

## Key Directories
- app.py: application entrypoint
- web/templates: HTML templates
- web/static: JS/CSS
- docs: requirements and tests
- tests: pytest suites
