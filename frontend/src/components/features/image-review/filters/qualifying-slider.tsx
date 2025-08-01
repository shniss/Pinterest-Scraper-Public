interface QualifyingSliderProps {
  qualifyingLevel: number
  onQualifyingLevelChange: (level: number) => void
}

export function QualifyingSlider({ qualifyingLevel, onQualifyingLevelChange }: QualifyingSliderProps) {
  return (
    <div className="flex items-center space-x-4">
      <span className="text-sm text-stone-600 font-medium">Qualifying Level:</span>
      <div className="flex items-center space-x-3">
        <span className="text-xs text-stone-500 w-8">0%</span>
        <input
          type="range"
          min="0"
          max="100"
          value={qualifyingLevel}
          onChange={(e) => onQualifyingLevelChange(Number(e.target.value))}
          className="w-32 h-2 bg-stone-200 rounded-lg appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, #ef4444 0%, #f59e0b ${qualifyingLevel}%, #10b981 ${qualifyingLevel}%, #10b981 100%)`,
          }}
        />
        <span className="text-xs text-stone-500 w-12">100%</span>
        <div className="bg-stone-50/90 backdrop-blur-sm border border-stone-200 rounded-lg px-3 py-1 w-16 text-center">
          <span className="text-sm font-medium text-stone-700">{qualifyingLevel}%</span>
        </div>
      </div>
    </div>
  )
} 