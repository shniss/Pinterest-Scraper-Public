"use client"

import type React from "react"
import { useState } from "react"
import { ImageReviewHeader } from "../image-review/image-review-header"
import { SearchResults } from "../image-review/search-results"
import { WarmupProgress } from "../progress/warmup-progress"
import { SearchLanding } from "./search-landing"

import { useSearchSession } from '../../../hooks/use-search-session'
import { useImageFilters } from '../../../hooks/use-image-filters'
import { isWarmupCompleteFromTaskUpdateMessages, getScrapedImagesFromTaskUpdateMessages, getValidationResultsFromTaskUpdateMessages } from '../../../lib/message-parser'
import { FilterType, ImageItem } from '../../../types/search'

/**
 * Main application component that orchestrates the entire search flow.
 * Handles search input, progress tracking, and results display.
 */
export function SearchApp() {
  // Local UI state
  const [query, setQuery] = useState("")
  const [isFocused, setIsFocused] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [searchError, setSearchError] = useState("")
  
  // Image filtering and sorting logic
  const {
    filterType,
    qualifyingLevel,
    showFilterDropdown,
    setFilterType,
    setQualifyingLevel,
    setShowFilterDropdown,
    getFilteredItems,
    getFilterLabel,
  } = useImageFilters()
  
  // WebSocket connection and search session management
  const {
    isSearching,
    promptId,
    allTaskUpdateMessages,
    warmupMessages,
    scrapedImagesMessages,
    validationMessages,
    error: backendError,
    isConnected,
    startSearchSession,
    stopSearchSession,
    clearError,
  } = useSearchSession()

  /**
   * Handles search form submission and initiates backend search
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Clear any previous error
    setSearchError("")
    clearError()
    
    // Validate that query is not empty
    if (!query.trim()) {
      setSearchError("Enter a prompt to get started")
      return
    }

    console.log("Form submitted with query:", query)

    // Start backend search via WebSocket
    try {
      await startSearchSession(query.trim())
    } catch (error) {
      console.error('Failed to start search:', error)
      setSearchError(error instanceof Error ? error.message : 'Failed to start search')
    }
  }

  /**
   * Resets the application state for a new search
   */
  const handleNewSearch = () => {
    stopSearchSession()
    setShowResults(false)
    setQuery("")
    setSearchError("")
  }

  // Transform scraped images and validation results into display-ready items
  const gridItems = scrapedImagesMessages.map((scrapedImage) => {
    // Find corresponding validation result for this image
    const validation = validationMessages.find(v => v.pin_id === scrapedImage.pin_id)
    
    if (validation) {
      // Image has been validated - show results
      return {
        id: scrapedImage.pin_id,
        description: validation.label,
        percentage: Math.round(validation.score * 100), // Convert 0-1 to 0-100
        isMatch: validation.valid,
        imageUrl: scrapedImage.url,
        sourceUrl: scrapedImage.pin_url,
        sourceName: "pinterest.com",
        isLoading: false,
        isEvaluating: false,
      }
    } else {
      // Image is still being evaluated - show loading state
      return {
        id: scrapedImage.pin_id,
        description: "Evaluating image...",
        percentage: 0,
        isMatch: false,
        imageUrl: scrapedImage.url,
        sourceUrl: scrapedImage.pin_url,
        sourceName: "pinterest.com",
        isLoading: false,
        isEvaluating: true,
      }
    }
  })

  // Determine when to show results based on warmup completion
  const warmupComplete = isWarmupCompleteFromTaskUpdateMessages(allTaskUpdateMessages)
  const hasScrapedImages = scrapedImagesMessages.length > 0
  
  // Auto-show results when warmup completes and we have scraped images
  if (warmupComplete && hasScrapedImages && !showResults) {
    setShowResults(true)
  }

  // Render different UI states based on application state
  if (showResults) {
    const filteredItems = getFilteredItems(gridItems)

    return (
      <div className="relative min-h-screen bg-stone-100 flex flex-col">
        <ImageReviewHeader
          query={query}
          onNewSearch={handleNewSearch}
          filteredItems={filteredItems}
          filterType={filterType}
          qualifyingLevel={qualifyingLevel}
          showFilterDropdown={showFilterDropdown}
          onFilterTypeChange={setFilterType}
          onQualifyingLevelChange={setQualifyingLevel}
          onShowFilterDropdownChange={setShowFilterDropdown}
          getFilterLabel={getFilterLabel}
        />

        <div className="flex-1 overflow-auto">
          <SearchResults filteredItems={filteredItems} query={query} qualifyingLevel={qualifyingLevel} />
        </div>

        {/* Dropdown overlay */}
        {/* Temporarily disabled to debug click issues */}
        {/* {showFilterDropdown && <div className="fixed inset-0 z-[150]" onClick={() => setShowFilterDropdown(false)} />} */}
      </div>
    )
  }

  if (isSearching) {
    return (
      <WarmupProgress
        query={query}
        messages={warmupMessages}
        isConnected={isConnected}
        error={backendError}
      />
    )
  }

  // Default state: show search landing page
  return (
    <SearchLanding
      query={query}
      setQuery={setQuery}
      isFocused={isFocused}
      setIsFocused={setIsFocused}
      onSubmit={handleSubmit}
      searchError={searchError}
    />
  )
}
