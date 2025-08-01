# Pinterest AI Agent Backend

A FastAPI-based backend service that automates Pinterest account warmup and image scraping using AI-powered validation. This service provides real-time WebSocket communication for progress tracking and integrates with Celery for background task processing.

## 🏗️ Architecture

### Core Technologies
- **FastAPI**
- **Celery** - Distributed task queue for background processing
- **Playwright** - Browser automation for Pinterest scraping
- **Motor** - Async MongoDB driver
- **Redis** - Message broker and caching
- **OpenAI GPT-4o-Mini Vision** - Relatively low-cost high performance image validation with simple integration through OpenAI API

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Celery        │
│   (React)       │◄──►│   (WebSocket)   │◄──►│   (Tasks)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MongoDB       │    │   Playwright    │
                       │   (Data Store)  │    │   (Browser)     │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── app.py                    # FastAPI application entry point
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py
│   │   ├── pin.py               # Pin data model
│   │   ├── pinterest_account.py # Pinterest account model
│   │   ├── prompt.py            # Prompt model
│   │   ├── session.py           # Session model
│   │   └── update_messages.py   # WebSocket message models
│   ├── routes/                  # API route handlers
│   │   ├── __init__.py
│   │   ├── prompts.py           # Prompt creation endpoint
│   │   └── websockets.py        # WebSocket endpoint
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── database/            # Database layer
│   │   │   └── repo.py          # Repository pattern implementation
|   |   |   |__ db.py            # Motor Mongodb database instance
│   │   ├── automation/          # Automation services
│   │   │   ├── browser_factory.py # Playwright browser management
│   │   │   ├── actions.py       # Pinterest automation actions
│   │   │   └── image_evaluator.py # AI image validation
│   │   └── messaging/           # Communication services
│   │       ├── broadcast.py     # WebSocket broadcasting for celery tasks
│   │       └── ws_manager.py    # WebSocket connection management
│   └── tasks/                   # Celery background tasks
│       ├── __init__.py
│       ├── warmup_and_scraping.py # Main Pinterest workflow
│       └── validation.py        # Image validation task
├── Dockerfile                   # Container configuration
├── pyproject.toml              # Python dependencies
└── poetry.lock                 # Locked dependency versions
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry (dependency management)
- MongoDB instance
- Redis instance
- OpenAI API key

### Installation

1. **Clone and navigate to backend directory:**
   ```bash
   cd pinterest-agent-platform/backend
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Install Playwright browsers:**
   ```bash
   poetry run playwright install
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
MONGODB_URL=mongodb://localhost:27017/pinterest_agent
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your_openai_api_key
```

### Running the Application

1. **Start Redis (required for Celery):**
   ```bash
   redis-server
   ```

2. **Start Celery worker:**
   ```bash
   poetry run celery -A app.services.celery_app worker --loglevel=info
   ```

3. **Start FastAPI server:**
   ```bash
   poetry run uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔌 API Endpoints

### REST Endpoints

#### `POST /prompts`
Create a new Pinterest scraping prompt.

**Request Body:**
```json
{
  "prompt": "modern minimalist interior design",
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "prompt_id": "generated_prompt_id",
  "status": "pending"
}
```

### WebSocket Endpoints

#### `WS /ws/{prompt_id}`
Real-time communication for task progress updates.

**Message Types:**
- `WarmupMessage` - Pinterest warmup progress
- `ScrapedImageMessage` - New image found
- `ValidationMessage` - AI validation results

## 🔄 Background Tasks

### Warmup and Scraping Task
**Task Name:** `app.tasks.warmup_and_scraping`

**Workflow:**
1. **Login Phase** - Authenticate with Pinterest
2. **Board Creation** - Create a new board for the prompt
3. **Pin Saving** - Save relevant pins to train recommendations
4. **Scraping Phase** - Extract images from "More Ideas"
5. **Database Storage** - Save extracted data
6. **Real-time Updates** - Broadcast progress via WebSocket

### Validation Task
**Task Name:** `app.tasks.validation`

**Workflow:**
1. **Image Retrieval** - Get pending images from database
2. **AI Evaluation** - Use OpenAI GPT-4o-mini Vision for scoring
3. **Score Processing** - Convert to 0-1 range
4. **Database Update** - Store validation results
5. **Frontend Broadcast** - Send results via WebSocket

## 🔧 Configuration

### Celery Configuration
- **Broker:** Redis
- **Result Backend:** Redis
- **Task Routing:** Automatic
- **Concurrency:** Configurable via worker processes

### Playwright Configuration
- **Browser:** Chromium (headless)
- **Viewport:** 1920x1080
- **User Agent:** Configurable per account
- **Proxy Support:** Optional

### AI Validation Configuration
- **Model:** OpenAI GPT-4 Vision
- **Timeout:** 30 seconds per image
- **Score Range:** 0-1 (normalized)
- **Prompt Engineering:** Optimized for image relevance


###Spec Deviations
- **Pin Collection Model** status includes not only "approved" and "disqualified" but "pending" for the period between an image being scraped and being evaluated