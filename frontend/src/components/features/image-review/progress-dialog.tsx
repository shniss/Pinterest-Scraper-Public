interface ProgressDialogProps {
  filteredItems: any[]
  
}

export function ProgressDialog({ filteredItems }: ProgressDialogProps) {
  return (
    <div className="bg-stone-50/90 backdrop-blur-sm border border-stone-200 rounded-xl px-4 py-2 shadow-sm">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1">
          <span className="text-xs font-medium text-stone-600">{filteredItems.length} results found</span>
        </div>
        <span className="text-xs text-stone-500">Sorted by relevance</span>
      </div>
    </div>
  )
} 