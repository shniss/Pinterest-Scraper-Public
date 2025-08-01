import { Button } from "@/components/ui/button"
import { ChevronDown } from "lucide-react"

interface FilterDropdownProps {
  filterType: "all" | "approved" | "disqualified"
  showFilterDropdown: boolean
  onFilterTypeChange: (type: "all" | "approved" | "disqualified") => void
  onShowFilterDropdownChange: (show: boolean) => void
  getFilterLabel: () => string
}

export function FilterDropdown({
  filterType,
  showFilterDropdown,
  onFilterTypeChange,
  onShowFilterDropdownChange,
  getFilterLabel,
}: FilterDropdownProps) {
  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          console.log('Dropdown button clicked, current state:', showFilterDropdown)
          onShowFilterDropdownChange(!showFilterDropdown)
        }}
        className="h-10 px-4 rounded-lg border-stone-300 bg-stone-50/80 hover:bg-stone-100 text-stone-600 hover:text-stone-700 transition-all duration-200"
      >
        {getFilterLabel()}
        <ChevronDown className="h-4 w-4 ml-2" />
      </Button>

      {showFilterDropdown && (
        <div className="absolute top-12 left-0 bg-stone-50/95 backdrop-blur-sm border border-stone-200 rounded-lg shadow-lg z-[200] min-w-[140px]">
          <div className="p-1">
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('All Results clicked')
                onFilterTypeChange("all")
                onShowFilterDropdownChange(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                filterType === "all"
                  ? "bg-stone-200/60 text-stone-800"
                  : "text-stone-600 hover:bg-stone-100/60"
              }`}
            >
              All Results
            </button>
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('Approved clicked')
                onFilterTypeChange("approved")
                onShowFilterDropdownChange(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                filterType === "approved"
                  ? "bg-stone-200/60 text-stone-800"
                  : "text-stone-600 hover:bg-stone-100/60"
              }`}
            >
              Approved
            </button>
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                console.log('Disqualified clicked')
                onFilterTypeChange("disqualified")
                onShowFilterDropdownChange(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                filterType === "disqualified"
                  ? "bg-stone-200/60 text-stone-800"
                  : "text-stone-600 hover:bg-stone-100/60"
              }`}
            >
              Disqualified
            </button>
          </div>
        </div>
      )}
    </div>
  )
} 