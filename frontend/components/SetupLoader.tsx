'use client'

import { Box, Typography, LinearProgress, Paper } from '@mui/material'
import { CheckCircle, Circle } from '@mui/icons-material'
import { useState, useEffect } from 'react'

interface SetupStep {
  label: string
  completed: boolean
}

export default function SetupLoader() {
  const [steps, setSteps] = useState<SetupStep[]>([
    { label: 'Validating your information...', completed: false },
    { label: 'Creating your company database...', completed: false },
    { label: 'Setting up your environment...', completed: false },
    { label: 'Initializing data structures...', completed: false },
    { label: 'Finalizing setup...', completed: false },
  ])

  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    // Simulate progressive completion
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < steps.length - 1) {
          const newSteps = [...steps]
          newSteps[prev].completed = true
          setSteps(newSteps)
          return prev + 1
        }
        return prev
      })
    }, 800)

    return () => clearInterval(interval)
  }, [])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        gap: 4,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 500,
          width: '100%',
          borderRadius: 2,
        }}
      >
        <Typography variant="h5" gutterBottom align="center" fontWeight={600}>
          Setting Up Your Workspace
        </Typography>
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Please wait while we prepare everything for you...
        </Typography>

        <Box sx={{ mb: 3 }}>
          <LinearProgress variant="determinate" value={(currentStep / steps.length) * 100} />
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {steps.map((step, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                opacity: index <= currentStep ? 1 : 0.4,
                transition: 'opacity 0.3s ease-in-out',
              }}
            >
              {step.completed ? (
                <CheckCircle color="success" />
              ) : index === currentStep ? (
                <Circle color="primary" sx={{ animation: 'pulse 1.5s ease-in-out infinite' }} />
              ) : (
                <Circle color="disabled" />
              )}
              <Typography variant="body2" color={step.completed ? 'success.main' : 'text.primary'}>
                {step.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Paper>

      <style jsx global>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </Box>
  )
}
