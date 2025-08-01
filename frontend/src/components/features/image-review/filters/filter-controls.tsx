import { FilterDropdown } from "./filter-dropdown"
import { QualifyingSlider } from "./qualifying-slider"

interface FilterControlsProps {
  filterType: "all" | "approved" | "disqualified"
  qualifyingLevel: number
  showFilterDropdown: boolean
  onFilterTypeChange: (type: "all" | "approved" | "disqualified") => void
  onQualifyingLevelChange: (level: number) => void
  onShowFilterDropdownChange: (show: boolean) => void
  getFilterLabel: () => string
}

export function FilterControls({
  filterType,
  qualifyingLevel,
  showFilterDropdown,
  onFilterTypeChange,
  onQualifyingLevelChange,
  onShowFilterDropdownChange,
  getFilterLabel,
}: FilterControlsProps) {
  return (
    <div className="flex items-center justify-between gap-6">
      <FilterDropdown
        filterType={filterType}
        showFilterDropdown={showFilterDropdown}
        onFilterTypeChange={onFilterTypeChange}
        onShowFilterDropdownChange={onShowFilterDropdownChange}
        getFilterLabel={getFilterLabel}
      />

      <QualifyingSlider
        qualifyingLevel={qualifyingLevel}
        onQualifyingLevelChange={onQualifyingLevelChange}
      />
    </div>
  )
} 