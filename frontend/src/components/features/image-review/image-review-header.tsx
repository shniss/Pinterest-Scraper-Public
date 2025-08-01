import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Plus,
  Download,
} from "lucide-react"
import { ReviewText } from "./review-text"
import { ProgressDialog } from "./progress-dialog"
import { FilterControls } from "./filters/filter-controls"

interface ImageReviewHeaderProps {
  query: string
  onNewSearch: () => void
  filteredItems: any[]
  filterType: "all" | "approved" | "disqualified"
  qualifyingLevel: number
  showFilterDropdown: boolean
  onFilterTypeChange: (type: "all" | "approved" | "disqualified") => void
  onQualifyingLevelChange: (level: number) => void
  onShowFilterDropdownChange: (show: boolean) => void
  getFilterLabel: () => string
}

/**
 * Header component for the image review interface.
 * Contains search query display, progress tracking, and filter controls.
 */
export function ImageReviewHeader({
  query,
  onNewSearch,
  filteredItems,
  filterType,
  qualifyingLevel,
  showFilterDropdown,
  onFilterTypeChange,
  onQualifyingLevelChange,
  onShowFilterDropdownChange,
  getFilterLabel,
}: ImageReviewHeaderProps) {
  return (
    <div className="flex-shrink-0 px-8 py-6 bg-stone-100/95 backdrop-blur-sm border-b border-stone-200/50 relative z-40">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between gap-6 mb-4">
          {/* Search query display */}
          <ReviewText query={query} />

          {/* Progress tracking dialog */}
          <ProgressDialog filteredItems={filteredItems} />

          {/* New search button */}
          <Button
            onClick={onNewSearch}
            variant="outline"
            size="sm"
            className="h-12 px-4 rounded-full border-stone-300 bg-stone-50/80 hover:bg-stone-100 text-stone-600 hover:text-stone-700 transition-all duration-200"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Search
          </Button>
        </div>

        {/* Filter controls */}
        <FilterControls
          filterType={filterType}
          qualifyingLevel={qualifyingLevel}
          showFilterDropdown={showFilterDropdown}
          onFilterTypeChange={onFilterTypeChange}
          onQualifyingLevelChange={onQualifyingLevelChange}
          onShowFilterDropdownChange={onShowFilterDropdownChange}
          getFilterLabel={getFilterLabel}
        />
      </div>
    </div>
  )
} 