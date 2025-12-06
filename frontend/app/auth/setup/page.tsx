'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { authAPI } from '@/lib/api'
import {
  Box,
  Container,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  MenuItem,
  Alert,
  Paper,
  AppBar,
  Toolbar,
  LinearProgress,
} from '@mui/material'
import { Upload as UploadIcon, Psychology as BrainIcon } from '@mui/icons-material'
import { ThemeToggle } from '@/components/ThemeToggle'
import SetupLoader from '@/components/SetupLoader'
import { useSnackbar } from '@/components/SnackbarProvider'

const steps = ['Company Details', 'Sustainability Targets', 'Budget & Data']

const industries = ['ITeS', 'Manufacturing', 'Hospitality']

export default function SetupPage() {
  const router = useRouter()
  const { user, refreshUser } = useAuth()
  const { showSnackbar } = useSnackbar()

  const [activeStep, setActiveStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showLoader, setShowLoader] = useState(false)

  // Form data
  const [industry, setIndustry] = useState('')
  const [location, setLocation] = useState('')
  const [targetYear, setTargetYear] = useState<number>(2030)
  const [renewablePercentage, setRenewablePercentage] = useState<number>(50)
  const [budget, setBudget] = useState<number>(0)
  const [csvFile, setCsvFile] = useState<File | null>(null)

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {}

    if (step === 0) {
      if (!industry) newErrors.industry = 'Industry is required'
      if (!location || location.length < 2) newErrors.location = 'Location must be at least 2 characters'
    } else if (step === 1) {
      if (targetYear < 2025 || targetYear > 2100) {
        newErrors.targetYear = 'Target year must be between 2025 and 2100'
      }
      if (renewablePercentage < 0 || renewablePercentage > 100) {
        newErrors.renewablePercentage = 'Percentage must be between 0 and 100'
      }
    } else if (step === 2) {
      if (budget <= 0) newErrors.budget = 'Budget must be greater than 0'
      if (!csvFile) newErrors.csvFile = 'Historical data CSV file is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prev) => prev + 1)
      setError('')
    }
  }

  const handleBack = () => {
    setActiveStep((prev) => prev - 1)
    setError('')
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setErrors({ ...errors, csvFile: 'File must be a CSV' })
        return
      }
      setCsvFile(file)
      setErrors({ ...errors, csvFile: '' })
    }
  }

  const handleSubmit = async () => {
    if (!validateStep(activeStep)) return

    setLoading(true)
    setShowLoader(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('industry', industry)
      formData.append('location', location)
      formData.append('sustainability_target_kp1', targetYear.toString())
      formData.append('sustainability_target_kp2', renewablePercentage.toString())
      formData.append('budget', budget.toString())

      if (csvFile) {
        formData.append('historical_data', csvFile)
      } else {
        throw new Error('Historical data file is required')
      }

      await authAPI.completeSetup(formData)

      // Wait for loader animation to complete
      await new Promise((resolve) => setTimeout(resolve, 4000))

      await refreshUser()
      showSnackbar('Setup completed successfully!', 'success')
      router.push('/dashboard')
    } catch (err: any) {
      setShowLoader(false)
      setError(err.response?.data?.detail || 'Setup failed. Please try again.')
      showSnackbar('Setup failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Check if user is admin
  if (user && !user.roles.includes('admin') && !user.roles.includes('super_admin')) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 4 }}>
          Access denied. Only admin users can access setup.
        </Alert>
      </Container>
    )
  }

  if (showLoader) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppBar position="fixed" sx={{ backgroundColor: 'background.paper', boxShadow: 1 }}>
          <Toolbar>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BrainIcon sx={{ fontSize: 32, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight={700} color="primary">
                AERO: AI for Energy Resource Optimization
              </Typography>
            </Box>
          </Toolbar>
        </AppBar>
        <Toolbar />
        <Container maxWidth="md" sx={{ mt: 8 }}>
          <SetupLoader />
        </Container>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Navigation */}
      <AppBar
        position="fixed"
        sx={{
          backgroundColor: 'background.paper',
          backdropFilter: 'blur(10px)',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
            <BrainIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(90deg, #2563eb 0%, #4f46e5 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AERO: AI for Energy Resource Optimization - Setup
            </Typography>
          </Box>
          <ThemeToggle />
        </Toolbar>
      </AppBar>

      <Toolbar />

      {/* Content */}
      <Container maxWidth="md" sx={{ mt: 8, mb: 8 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Typography variant="h4" gutterBottom fontWeight={700} align="center">
            Welcome! Let's Set Up Your Company Profile
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
            Complete these steps to create your personalized workspace
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {loading && <LinearProgress sx={{ mb: 3 }} />}

          {/* Step 0: Company Details */}
          {activeStep === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <TextField
                select
                label="Industry *"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                error={!!errors.industry}
                helperText={errors.industry}
                fullWidth
              >
                {industries.map((ind) => (
                  <MenuItem key={ind} value={ind}>
                    {ind}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                label="Location *"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                error={!!errors.location}
                helperText={errors.location || 'e.g., Mumbai, India'}
                fullWidth
              />
            </Box>
          )}

          {/* Step 1: Sustainability Targets */}
          {activeStep === 1 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <TextField
                type="number"
                label="Sustainability Target KP1 - Target Year for Zero Non-Renewable *"
                value={targetYear}
                onChange={(e) => setTargetYear(parseInt(e.target.value))}
                error={!!errors.targetYear}
                helperText={errors.targetYear || 'Target year to achieve zero non-renewable energy (2025-2100)'}
                fullWidth
                inputProps={{ min: 2025, max: 2100 }}
              />

              <TextField
                type="number"
                label="Sustainability Target KP2 - Percentage Increase in Renewable Mix *"
                value={renewablePercentage}
                onChange={(e) => setRenewablePercentage(parseFloat(e.target.value))}
                error={!!errors.renewablePercentage}
                helperText={errors.renewablePercentage || 'Target percentage increase in renewable energy (0-100%)'}
                fullWidth
                inputProps={{ min: 0, max: 100, step: 0.1 }}
              />
            </Box>
          )}

          {/* Step 2: Budget & Historical Data */}
          {activeStep === 2 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <TextField
                type="number"
                label="Budget *"
                value={budget}
                onChange={(e) => setBudget(parseFloat(e.target.value))}
                error={!!errors.budget}
                helperText={errors.budget || 'Annual budget for sustainability initiatives'}
                fullWidth
                inputProps={{ min: 0, step: 1000 }}
              />

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                    Historical Data *
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Upload a CSV file with your historical energy consumption data
                  </Typography>

                  <input
                    accept=".csv"
                    style={{ display: 'none' }}
                    id="csv-upload"
                    type="file"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="csv-upload">
                    <Button
                      variant="outlined"
                      component="span"
                      startIcon={<UploadIcon />}
                      fullWidth
                    >
                      {csvFile ? csvFile.name : 'Choose CSV File'}
                    </Button>
                  </label>

                  {errors.csvFile && (
                    <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                      {errors.csvFile}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Navigation Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button disabled={activeStep === 0 || loading} onClick={handleBack}>
              Back
            </Button>
            <Box sx={{ flex: '1 1 auto' }} />
            {activeStep === steps.length - 1 ? (
              <Button variant="contained" onClick={handleSubmit} disabled={loading}>
                Complete Setup
              </Button>
            ) : (
              <Button variant="contained" onClick={handleNext} disabled={loading}>
                Next
              </Button>
            )}
          </Box>
        </Paper>
      </Container>
    </Box>
  )
}
