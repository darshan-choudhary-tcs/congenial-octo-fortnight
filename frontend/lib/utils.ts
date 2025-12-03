import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFileSize(bytes: number) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

export function getConfidenceColor(confidence: number) {
  if (confidence >= 0.8) return 'text-green-600'
  if (confidence >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

export function getConfidenceLabel(confidence: number) {
  if (confidence >= 0.85) return 'Very High ' + confidence.toFixed(2)
  if (confidence >= 0.70) return 'High ' + confidence.toFixed(2)
  if (confidence >= 0.50) return 'Good ' + confidence.toFixed(2)
  if (confidence >= 0.40) return 'Moderate ' + confidence.toFixed(2)
  if (confidence >= 0.30) return 'Low ' + confidence.toFixed(2)
  return 'Very Low '
}
