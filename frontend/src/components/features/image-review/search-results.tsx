import { Button } from "@/components/ui/button"
import { Check, X, ExternalLink, Loader2 } from "lucide-react"

interface SearchResultsProps {
  filteredItems: any[]
  query: string
  qualifyingLevel: number
}

export function SearchResults({ filteredItems, query, qualifyingLevel }: SearchResultsProps) {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-1000">
        <div className="max-w-7xl mx-auto px-8 py-6">
          {filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-stone-500 text-lg">No results match the current filter criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredItems.map((item, displayIndex) => (
                <div
                  key={item.id}
                  className="bg-stone-50/80 rounded-xl border border-stone-200/60 hover:border-stone-300/80 transition-all duration-300 hover:shadow-lg group cursor-pointer overflow-hidden relative"
                  style={{
                    animationDelay: `${displayIndex * 50}ms`,
                  }}
                >
                  {/* Image */}
                  <div className="aspect-square relative overflow-hidden">
                    <img
                      src={item.imageUrl || "/placeholder.svg"}
                      alt={item.description}
                      className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${
                        item.isEvaluating ? 'blur-sm' : ''
                      }`}
                    />

                    {/* Loading overlay for evaluating images */}
                    {item.isEvaluating && (
                      <div className="absolute inset-0 bg-stone-100/80 backdrop-blur-sm flex items-center justify-center">
                        <div className="flex flex-col items-center space-y-3">
                          <Loader2 className="h-6 w-6 text-stone-500 animate-spin" />
                          <span className="text-xs text-stone-500 font-medium">Evaluating...</span>
                        </div>
                      </div>
                    )}

                    {/* Match indicator overlay */}
                    {!item.isEvaluating && (
                      <div className="absolute top-3 right-3 flex items-center space-x-2">
                        <div className="bg-stone-900/80 backdrop-blur-sm rounded-full px-2 py-1 flex items-center space-x-1">
                          <span className="text-xs font-medium text-stone-100">{item.percentage}%</span>
                          {item.percentage >= qualifyingLevel ? (
                            <Check className="h-3 w-3 text-green-400" />
                          ) : (
                            <X className="h-3 w-3 text-red-400" />
                          )}
                        </div>
                      </div>
                    )}

                    {/* External link button */}
                    {!item.isEvaluating && (
                      <div className="absolute top-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <Button
                          size="sm"
                          variant="secondary"
                          className="h-8 w-8 p-0 rounded-full bg-stone-50/90 hover:bg-stone-100/90 backdrop-blur-sm border border-stone-200/60"
                          onClick={(e) => {
                            e.stopPropagation()
                            window.open(item.sourceUrl, "_blank", "noopener,noreferrer")
                          }}
                        >
                          <ExternalLink className="h-3 w-3 text-stone-600" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Description and source */}
                  <div className="p-4">
                    <p className="text-sm font-light text-stone-600 leading-relaxed mb-2">{item.description}</p>
                    {!item.isEvaluating && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-stone-400 font-medium">{item.sourceName}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-xs text-stone-500 hover:text-stone-700 hover:bg-stone-200/60"
                          onClick={(e) => {
                            e.stopPropagation()
                            window.open(item.sourceUrl, "_blank", "noopener,noreferrer")
                          }}
                        >
                          View source
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 