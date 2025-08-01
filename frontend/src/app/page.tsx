import { SearchApp } from "../components/features/search/search-app"
import { ErrorBoundary } from "../components/error-boundary"

/**
 * Main page component for the Pinterest Agent Platform.
 * Renders the search application with error boundary protection.
 */
export default function Home() {
  return (
    <div
      className="relative min-h-screen overflow-hidden bg-stone-100"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fillRule='evenodd'%3E%3Cg fill='%23d6d3d1' fillOpacity='0.1'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
      }}
    >
      {/* Subtle texture overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-stone-50/50 via-neutral-50/30 to-stone-100/50"></div>

      {/* Main application with error boundary */}
      <ErrorBoundary>
        <SearchApp />
      </ErrorBoundary>
    </div>
  )
}
