export interface SearchState {
  query: string
  isSearching: boolean
  error: string | null
}

export type FilterType = "all" | "approved" | "disqualified"

export interface ImageItem {
  id: string
  description: string
  percentage: number
  isMatch: boolean
  imageUrl: string
  sourceUrl: string
  sourceName: string
  isLoading: boolean
  isEvaluating: boolean
} 