<h1 align="center">✅ Task Management API</h1>

<p align="center">
  <em>A clean, production-ready REST API for managing tasks, built with modern Python.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

---

## ✨ Features

- 🔐 **Auth-ready** — pluggable authentication layer
- 📝 **Full CRUD** — create, read, update, delete tasks
- 🏷️ **Rich task model** — priority, status, due dates, tags
- 📊 **Filtering & sorting** — query by status, priority, deadline
- 📖 **Auto-generated docs** — Swagger UI + ReDoc out of the box
- 🧪 **Tested** — covered by a solid test suite

## 🚀 Quick Start

```bash
git clone https://github.com/Hayrapetyan-Anri/task-management-api.git
cd task-management-api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for interactive API docs.

## 📡 Endpoints

| Method | Route              | Description              |
|--------|--------------------|--------------------------|
| GET    | `/tasks`           | List all tasks           |
| POST   | `/tasks`           | Create a new task        |
| GET    | `/tasks/{id}`      | Get a single task        |
| PUT    | `/tasks/{id}`      | Update a task            |
| DELETE | `/tasks/{id}`      | Delete a task            |

## 🧰 Tech Stack

**FastAPI** · **Pydantic** · **SQLAlchemy** · **PostgreSQL / SQLite** · **Pytest**

## 📂 Project Structure

```
task-management-api/
├── app/
│   ├── main.py          # FastAPI entrypoint
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── tests/
└── requirements.txt
```

## 📝 License

MIT © [Anri Hayrapetyan](https://anridev.com)
