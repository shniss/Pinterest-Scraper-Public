import { useState, useCallback } from 'react'
import { FilterType, ImageItem } from '../types/search'

/**
 * Custom hook for managing image filtering and sorting logic.
 * Provides filter state and functions for filtering images by approval status.
 */
export function useImageFilters() {
  // Filter state
  const [filterType, setFilterType] = useState<FilterType>("all")
  const [qualifyingLevel, setQualifyingLevel] = useState(70)
  const [showFilterDropdown, setShowFilterDropdown] = useState(false)

  /**
   * Filters and sorts images based on current filter settings
   */
  const getFilteredItems = useCallback((items: ImageItem[]) => {
    let filteredItems: ImageItem[]
    
    console.log(`Filtering with type: ${filterType}, qualifyingLevel: ${qualifyingLevel}`)
    console.log(`Total items: ${items.length}`)
    console.log(`Evaluating items: ${items.filter(item => item.isEvaluating).length}`)
    console.log(`Evaluated items: ${items.filter(item => !item.isEvaluating).length}`)
    
    switch (filterType) {
      case "approved":
        // Show only images that meet the qualifying threshold
        filteredItems = items.filter((item) => !item.isEvaluating && item.percentage >= qualifyingLevel)
        console.log(`Approved items: ${filteredItems.length}`)
        break
      case "disqualified":
        // Show only images below the qualifying threshold
        filteredItems = items.filter((item) => !item.isEvaluating && item.percentage < qualifyingLevel)
        console.log(`Disqualified items: ${filteredItems.length}`)
        break
      default:
        // Show all images
        filteredItems = items
        console.log(`All items: ${filteredItems.length}`)
    }
    
    // Sort by percentage (highest to lowest)
    return filteredItems.sort((a, b) => b.percentage - a.percentage)
  }, [filterType, qualifyingLevel])

  /**
   * Returns the display label for the current filter type
   */
  const getFilterLabel = useCallback(() => {
    switch (filterType) {
      case "approved":
        return "Approved"
      case "disqualified":
        return "Disqualified"
      default:
        return "All Results"
    }
  }, [filterType])

  return {
    filterType,
    qualifyingLevel,
    showFilterDropdown,
    setFilterType,
    setQualifyingLevel,
    setShowFilterDropdown,
    getFilteredItems,
    getFilterLabel,
  }
} 