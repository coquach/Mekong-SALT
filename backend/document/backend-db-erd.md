# Backend Database ERD (PlantUML)

This document describes the backend relational schema using PlantUML.

## Files

- `backend/document/backend-db-erd.puml`: Full ERD source.

## Scope

The ERD is generated from current SQLAlchemy models in `backend/app/models` and includes:

- Core operational domain (`regions`, sensors, weather, risk, incidents, actions)
- Workflow and observability (`approvals`, decisions, audits, notifications, agent runs)
- Knowledge base tables (`knowledge_documents`, `embedded_chunks`)
- Primary/foreign keys, important unique constraints, and key checks

## Render

Option 1: VS Code PlantUML extension

1. Open `backend/document/backend-db-erd.puml`.
2. Use preview (`Alt+D`) or export command from the extension.

Option 2: PlantUML CLI

```bash
cd backend/document
plantuml backend-db-erd.puml
```

This generates `backend-db-erd.png` (and/or SVG depending on your PlantUML setup).
