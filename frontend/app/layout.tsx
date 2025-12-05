import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { ThemeProvider } from '@/lib/theme-context'
import { SnackbarProvider } from '@/components/SnackbarProvider'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter'

export const metadata: Metadata = {
  title: 'AERO: AI for Energy Resource Optimization',
  description: 'Advanced AI system with RAG, Multi-Agent orchestration, and Explainable AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="emotion-insertion-point" content="" />
      </head>
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider>
            <AuthProvider>
              {children}
              <SnackbarProvider />
            </AuthProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
