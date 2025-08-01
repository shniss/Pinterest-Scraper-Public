import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

interface ReviewTextProps {
  query: string
}

export function ReviewText({ query }: ReviewTextProps) {
  return (
    <div className="flex-1 max-w-2xl">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
          <Search className="h-4 w-4 text-stone-400" />
        </div>
        <Input
          type="text"
          value={query}
          readOnly
          className="h-12 rounded-full border border-stone-300 bg-stone-50/80 backdrop-blur-sm pl-12 pr-4 text-base font-light tracking-wide text-stone-600 select-none focus:ring-0 focus:border-stone-300 focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
      </div>
    </div>
  )
} 