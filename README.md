# Telegram Leads System

Modern CRM system for managing leads from Telegram bots with automatic distribution and real-time notifications.

## Features

- **Multi-bot support** - manage multiple Telegram bots in one system
- **Smart distribution** - automatic round-robin lead assignment between managers
- **Real-time chat** - WebSocket-based instant messaging with leads
- **Analytics dashboard** - track performance metrics and statistics
- **Role-based access** - admin and manager roles with project isolation
- **Auto-replies** - customizable welcome messages for each bot

## Tech Stack

**Backend**
- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- WebSockets
- JWT Authentication

**Frontend**
- React 18
- TypeScript
- Vite
- Axios
- Pinia (state management)

**Infrastructure**
- Docker & Docker Compose
- Nginx (production)

## Quick Start

1. Clone the repository
```bash
git clone https://github.com/your-username/telegram-leads.git
cd telegram-leads
```

2. Configure environment
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

3. Launch with Docker
```bash
docker-compose up -d
```

4. Access the application
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Project Structure
```
telegram-leads/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models.py     # Database models
│   │   ├── auth.py       # Authentication
│   │   └── telegram_handler.py
│   ├── tests/            # Test suite
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── stores/
│   └── Dockerfile
└── docker-compose.yml
```

## API Endpoints

**Authentication**
- `POST /auth/login` - manager login
- `GET /auth/me` - get current user

**Leads**
- `GET /leads` - list leads (filtered by manager)
- `GET /leads/{id}` - lead details
- `PUT /leads/{id}/close` - close lead

**Messages**
- `GET /leads/{id}/messages` - chat history
- `POST /leads/{id}/messages` - send message
- `WebSocket /ws` - real-time updates

**Admin**
- `POST /managers` - create manager
- `POST /projects` - create project
- `POST /bots` - create bot
- `GET /stats` - analytics data

## Development

**Run tests**
```bash
cd backend
pytest
```

**Database migrations**
```bash
cd backend
alembic upgrade head
```

## Configuration

Key environment variables in `backend/.env`:
```env
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@db:5432/leads_db
HOST=0.0.0.0
PORT=8000
```

## License

MIT

## Author

Built with FastAPI and React