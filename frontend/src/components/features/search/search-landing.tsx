import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search } from "lucide-react"
import { AnimatedText } from "./animated-text"

interface SearchLandingProps {
  query: string
  setQuery: (query: string) => void
  isFocused: boolean
  setIsFocused: (focused: boolean) => void
  onSubmit: (e: React.FormEvent) => void
  searchError: string
}

/**
 * Landing page component for the search interface.
 * Displays the main search form with animated text and error handling.
 */
export function SearchLanding({
  query,
  setQuery,
  isFocused,
  setIsFocused,
  onSubmit,
  searchError,
}: SearchLandingProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      {/* Main title with "Find" text */}
      <div className="text-center mb-12">
        <h1 className="font-playfair text-6xl font-black uppercase tracking-[0.15em] text-stone-800 mb-6 md:text-7xl lg:text-8xl italic">
          Find
        </h1>
        <AnimatedText />
      </div>

      {/* Search form */}
      <form onSubmit={onSubmit} className="w-full max-w-2xl">
        <div className="relative">
          <Input
            type="text"
            placeholder="Describe the images you're looking for..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className={`h-16 text-lg px-6 pr-16 rounded-full border-2 transition-all duration-300 ${
              isFocused
                ? "border-stone-400 shadow-lg shadow-stone-200/50"
                : "border-stone-300 shadow-md"
            }`}
          />
          
          {/* Search button */}
          <Button
            type="submit"
            className="absolute right-2 top-2 h-12 w-12 p-0 rounded-full bg-stone-600 hover:bg-stone-700 transition-colors"
          >
            <Search className="h-5 w-5" />
          </Button>
        </div>

        {/* Error message display */}
        {searchError && (
          <div className="mt-4 text-center">
            <p className="text-red-600 text-sm">{searchError}</p>
          </div>
        )}
      </form>

      {/* Example prompts */}
      <div className="mt-12 text-center">
        <p className="text-stone-600 mb-4">Try searching for:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {[
            "cottagecore aesthetics",
            "modern minimalist kitchen",
            "scandinavian living room",
            "industrial bathroom design"
          ].map((example) => (
            <button
              key={example}
              onClick={() => setQuery(example)}
              className="px-4 py-2 text-sm bg-stone-100 hover:bg-stone-200 rounded-full text-stone-700 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
} 