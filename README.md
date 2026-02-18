# Security Incident Triage Dashboard for M365 Alerts

A full-stack web application for ingesting, correlating, and triaging security alerts from Microsoft 365 and other security sources.

## Live Demo (coming soon)
- Demo: 
- Demo credentials: 

# Screenshots
- ![Dashboard & high-priority queue](docs/screenshots/dashboard.png)
- ![Incident details](docs/screenshots/incident-detail.png)
- ![Alerts](docs/screenshots/alerts.png)
- ![Upload Data](docs/screenshots/upload-data.png)

## Features

- **Data Ingestion**: Upload JSON/CSV alert files via drag-and-drop UI
- **Normalization**: Converts various alert formats to unified schema
- **Correlation**: Groups related alerts into incidents by entity overlap and time proximity
- **Triage Scoring**: Priority scores (0-100) with full explainability
- **Analyst Workflow**: Status tracking (New → Investigating → Contained → Closed)
- **Dashboard**: High-priority queue, filters, incident details
- **Reports**: Export incidents as Markdown

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

API available at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`

### Load Demo Data

Click "Upload Data" → "Load Demo Dataset" in the UI, or:

```bash
curl -X POST http://localhost:8000/api/seed
```

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────┐
│   React     │────▶│  FastAPI Backend                        │
│   Frontend  │     │  ┌─────────┐ ┌────────┐ ┌────────────┐  │
│             │◀────│  │Ingestion│─│Normalize│─│Correlation │  │
│  Dashboard  │     │  └─────────┘ └────────┘ └────────────┘  │
│  + Reports  │     │                    │                    │
└─────────────┘     │                    ▼                    │
                    │  ┌──────────────────────────────────┐   │
                    │  │     SQLite Database              │   │
                    │  └──────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, Pydantic
- **Frontend**: React 18, TypeScript, React Router, Vite

## Project Structure

```
├── backend/          # FastAPI application
├── frontend/         # React application
├── demo-data/        # Sample alert files
└── docs/             # Architecture, threat model, API docs
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Threat Model](docs/threat-model.md)

## License

MIT
