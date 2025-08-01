## Frontend Technology and Architecture

### Core Technologies
- **Next.js 15**
- **React**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **WebSockets**

### Application Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User          │    │   React App     │    │   Backend       │
│   Interface     │◄──►│   (Next.js)     │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   WebSocket     │
                       │   (Real-time)   │
                       └─────────────────┘
```

### Frontend Structure

Frontend runs as a single page app which updates state based off of incoming websocket messages
This works great for a simple search -> warmup -> review flow, allowing dynamic real-time updates from long-running backend tasks
In the future, it makes sense to break this into 3 pages for search warmup and review and create corresponding fastapi endpoints to provide
the data for displaying these. This makes it much easier to do things like session histories or sharing / revisiting previous searches
The database collections are already set up to make it easier to return all pins for a given session.




## Backend Technology and Architecture

### Core Technologies
- **FastAPI**
- **Celery** 
- **Playwright**
- **Motor**
- **Redis**
- **OpenAI GPT-4o-Mini Vision**

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