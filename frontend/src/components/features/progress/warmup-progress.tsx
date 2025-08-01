import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { WarmupMessage } from "../../../types/messages"
import { useEffect, useRef } from "react"

interface WarmupProgressProps {
  query: string
  messages: WarmupMessage[]
  isConnected: boolean
  error: string | null
}

export function WarmupProgress({ query, messages, isConnected, error }: WarmupProgressProps) {
  // Get the most recent message for main display
  const latestMessage = messages.length > 0 ? messages[messages.length - 1] : null
  
  // Get all other messages for the list (excluding the most recent)
  const listMessages = messages.length > 1 ? messages.slice(0, -1).reverse() : []
  
  // Determine connection status
  const getStatusText = () => {
    if (error) return error
    if (!isConnected) return "Connecting..."
    if (!latestMessage) return "Starting search..."
    return latestMessage.message
  }

  const getStatusColor = () => {
    if (error) return "text-red-600"
    if (!isConnected) return "text-yellow-600"
    if (latestMessage?.message.includes('successfully')) return "text-green-600"
    return "text-stone-600"
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-8">
      <div className="w-full max-w-2xl text-center">
        {/* Compact search bar */}
        <div className="mb-8">
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

        {/* Progress indicator */}
        <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-700">
          <div className="bg-stone-50/90 backdrop-blur-sm border border-stone-200 rounded-2xl p-8 shadow-lg">
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2">
                <div className={`h-2 w-2 rounded-full animate-pulse ${isConnected ? 'bg-green-500' : 'bg-stone-400'}`}></div>
                <div
                  className={`h-2 w-2 rounded-full animate-pulse ${isConnected ? 'bg-green-500' : 'bg-stone-400'}`}
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className={`h-2 w-2 rounded-full animate-pulse ${isConnected ? 'bg-green-500' : 'bg-stone-400'}`}
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </div>
              <p className={`text-lg font-light tracking-wide ${getStatusColor()}`}>
                {getStatusText()}
              </p>
              
              {/* Message history list */}
              {listMessages.length > 0 && (
                <div className="mt-6">
                  <div className="text-xs font-medium text-stone-400 mb-3 uppercase tracking-wider">
                    Progress Log
                  </div>
                  <div className="max-h-48 overflow-y-auto space-y-2 pr-2" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                    <style jsx>{`
                      div::-webkit-scrollbar {
                        display: none;
                      }
                    `}</style>
                    {listMessages.map((msg, index) => (
                      <div
                        key={`${msg.message}-${index}`}
                        className="animate-in slide-in-from-top-20 duration-1000 ease-out"
                        style={{ 
                          animationDelay: '0ms',
                          animationFillMode: 'both'
                        }}
                      >
                        <div className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg border border-stone-100 shadow-sm hover:shadow-md transition-all duration-200">
                          <div className="flex-shrink-0 w-2 h-2 rounded-full bg-stone-300 mt-2"></div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-stone-700 leading-relaxed">
                              {msg.message}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 