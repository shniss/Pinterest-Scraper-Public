# Pinterest AI Agent Frontend

## Architecture

### Core Technologies
- **Next.js 15** - React framework with App Router
- **React 19** - Modern React with concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality React components
- **WebSocket** - Real-time communication with backend
- **Zod** - Schema validation and type inference

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

## Project Structure

```
frontend/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── globals.css             # Global styles
│   │   ├── layout.tsx              # Root layout
│   │   └── page.tsx                # Home page
│   ├── components/                 # React components
│   │   ├── error-boundary.tsx      # Error boundary wrapper
│   │   ├── ui/                     # shadcn/ui components
│   │   │   ├── button.tsx          # Button component
│   │   │   └── input.tsx           # Input component
│   │   └── features/               # Feature-specific components
│   │       ├── search/             # Search functionality
│   │       │   ├── search-app.tsx  # Main search application
│   │       │   ├── search-landing.tsx # Landing page
│   │       │   └── animated-text.tsx # Animated text component
│   │       ├── image-review/       # Image review functionality
│   │       │   ├── search-results.tsx # Image grid display
│   │       │   ├── image-review-header.tsx # Header component
│   │       │   ├── review-text.tsx # Review text component
│   │       │   ├── progress-dialog.tsx # Progress dialog
│   │       │   └── filters/        # Filter components
│   │       │       ├── filter-controls.tsx # Filter controls
│   │       │       ├── filter-dropdown.tsx # Filter dropdown
│   │       │       └── qualifying-slider.tsx # Rating slider
│   │       └── progress/           # Progress components
│   │           └── warmup-progress.tsx # Warmup progress
│   ├── hooks/                      # Custom React hooks
│   │   ├── use-search-session.ts   # Search session management
│   │   └── use-image-filters.ts    # Image filtering logic
│   ├── lib/                        # Utility libraries
│   │   ├── api.ts                  # API client
│   │   ├── message-parser.ts       # WebSocket message parsing
│   │   ├── utils.ts                # Utility functions
│   │   └── websocket.ts            # WebSocket client
│   └── types/                      # TypeScript type definitions
│       ├── messages.ts             # WebSocket message types
│       └── search.ts               # Search-related types
├── public/                         # Static assets
├── package.json                    # Dependencies and scripts
├── tailwind.config.ts              # Tailwind configuration
├── next.config.mjs                 # Next.js configuration
├── tsconfig.json                   # TypeScript configuration
└── components.json                 # shadcn/ui configuration
```

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm, yarn, or pnpm
- Backend service running (see backend README)

### Installation

1. **Clone and navigate to frontend directory:**
   ```bash
   cd pinterest-agent-platform/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

5. **Open your browser:**
   ```
   http://localhost:3000
   ```

## UI Components

### Core Components

#### SearchApp
The main application component that orchestrates the entire search workflow.

**Features:**
- Real-time WebSocket communication
- Progress tracking and status updates
- Image filtering and sorting
- Error handling and recovery

#### SearchLanding
The initial landing page with search input and prompt entry.

#### SearchResults
Displays the grid of scraped images with filtering capabilities.

**Features:**
- Responsive image grid
- Loading states and spinners
- Rating display (0-100%)
- Filter controls
- Pinterest link integration

### Filter Components

#### FilterControls
Manages the overall filtering state and controls.

#### FilterDropdown
Dropdown for filtering by approval status (All/Approved/Denied).

#### QualifyingSlider
Slider for setting the minimum rating threshold (0-100%).

## 🔌 API Integration

### REST API Client
Located in `src/lib/api.ts`, handles HTTP requests to the backend.

### WebSocket Client
Located in `src/lib/websocket.ts`, manages real-time communication.

**Message Types:**
```typescript
interface WarmupMessage {
  type: "warmup";
  message: string;
}

interface ScrapedImageMessage {
  type: "scraped_image";
  pin_id: string;
  image_title: string;
  url: string;
  pin_url: string;
}

interface ValidationMessage {
  type: "validation";
  pin_id: string;
  score: number; // 0-1 range
  label: string;
  valid: boolean;
}
```

## User Workflow

### 1. Search Initiation
1. User enters a search prompt (e.g., "modern minimalist interior design")
2. System creates a new session and prompt
3. Backend starts Pinterest warmup process
4. Real-time progress updates via WebSocket

### 2. Warmup Phase
1. Pinterest account login
2. Board creation with prompt name
3. Pin saving to train recommendations
4. Progress displayed in real-time

### 3. Scraping Phase
1. Navigation to "More Ideas" page
2. Image extraction and processing
3. Database storage
4. Real-time image display in grid

### 4. Validation Phase
1. AI-powered image scoring
2. Score conversion (0-1 to 0-100%)
3. Visual indicators (checkmarks, ratings)
4. Filtering and sorting options
