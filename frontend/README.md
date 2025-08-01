# Pinterest AI Agent Frontend

A modern React/Next.js frontend application that provides a real-time interface for Pinterest image scraping and AI-powered validation. Built with TypeScript, Tailwind CSS, and shadcn/ui components for a professional user experience.

## 🏗️ Architecture

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

## 📁 Project Structure

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

## 🚀 Quick Start

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

### Environment Variables

Create a `.env.local` file with the following variables:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your_analytics_id
```

## 🎨 UI Components

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

**Features:**
- Clean, modern search interface
- Input validation
- Animated text effects
- Responsive design

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

**Key Methods:**
```typescript
// Create a new search prompt
createPrompt(prompt: string, sessionId: string): Promise<CreatePromptResponse>

// Get prompt status
getPromptStatus(promptId: string): Promise<PromptStatus>
```

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

## 🎯 User Workflow

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

## 🎨 Styling

### Tailwind CSS
- Utility-first CSS framework
- Responsive design system
- Dark/light mode support
- Custom component variants

### shadcn/ui
- High-quality React components
- Consistent design system
- Accessibility built-in
- Customizable theming

### Custom Styles
```css
/* Global styles in src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom component styles */
@layer components {
  .search-card {
    @apply bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow;
  }
}
```

## 🔧 Configuration

### Next.js Configuration
```javascript
// next.config.mjs
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}
```

### Tailwind Configuration
```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom color palette
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 🧪 Testing

### Unit Tests
```bash
npm run test
# or
yarn test
```

### E2E Tests
```bash
npm run test:e2e
# or
yarn test:e2e
```

### Component Testing
```bash
npm run test:components
# or
yarn test:components
```

## 📱 Responsive Design

### Breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

### Mobile-First Approach
- Touch-friendly interactions
- Optimized image loading
- Responsive grid layouts
- Accessible navigation

## ♿ Accessibility

### WCAG 2.1 Compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode
- Focus management

### ARIA Labels
- Semantic HTML structure
- Proper ARIA attributes
- Descriptive alt text
- Role definitions

## 🚀 Performance

### Optimization Strategies
- **Code Splitting** - Automatic route-based splitting
- **Image Optimization** - Next.js Image component
- **Bundle Analysis** - Webpack bundle analyzer
- **Lazy Loading** - Component and image lazy loading

### Performance Monitoring
```bash
# Build analysis
npm run build
npm run analyze

# Lighthouse audit
npm run lighthouse
```

## 🔒 Security

### Best Practices
- **Input Validation** - Zod schema validation
- **XSS Prevention** - React's built-in protection
- **CSRF Protection** - Next.js CSRF tokens
- **Content Security Policy** - CSP headers

### Environment Variables
- Client-side variables prefixed with `NEXT_PUBLIC_`
- Server-side secrets kept secure
- No sensitive data in client bundle

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t pinterest-agent-frontend .
```

### Run Container
```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  -e NEXT_PUBLIC_WS_URL=ws://backend:8000 \
  pinterest-agent-frontend
```

## 📊 Analytics

### Built-in Analytics
- Page view tracking
- User interaction events
- Performance metrics
- Error tracking

### Custom Events
```typescript
// Track search events
trackEvent('search_initiated', { prompt: searchPrompt });

// Track filter usage
trackEvent('filter_applied', { filterType, value });
```

## 🚨 Error Handling

### Error Boundaries
- React Error Boundary for component errors
- Graceful fallback UI
- Error reporting and logging

### Network Errors
- WebSocket reconnection logic
- API retry mechanisms
- Offline state handling

### User Feedback
- Toast notifications
- Loading states
- Error messages
- Success confirmations

## 🔄 State Management

### React Hooks
- **useState** - Local component state
- **useEffect** - Side effects and cleanup
- **useContext** - Global state sharing
- **Custom Hooks** - Reusable logic

### State Structure
```typescript
interface SearchState {
  isSearching: boolean;
  progress: number;
  images: ImageItem[];
  filters: FilterState;
  error: string | null;
}
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Type checking
- **Husky** - Git hooks

### Commit Convention
```
feat: add new search feature
fix: resolve WebSocket connection issue
docs: update README
style: format code with prettier
refactor: extract reusable hook
test: add unit tests for search component
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the component documentation
- Join the community discussions
