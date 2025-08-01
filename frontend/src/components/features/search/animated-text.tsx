"use client"

import { useState, useEffect } from "react"

const phrases = ["INSPIRATION","STYLES", "AESTHETICS"]

export function AnimatedText() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setIsVisible(false)

      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % phrases.length)
        setIsVisible(true)
      }, 500)
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <h2
      className={`font-sans text-7xl font-black uppercase tracking-[0.15em] text-stone-800 md:text-8xl lg:text-9xl transition-all duration-500 ease-in-out ${
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
    >
      {phrases[currentIndex]}
    </h2>
  )
}
