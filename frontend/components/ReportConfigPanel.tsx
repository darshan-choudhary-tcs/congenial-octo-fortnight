import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  TextField,
  Button,
  Grid,
  Collapse,
  IconButton,
  Alert,
  Chip,
  Divider,
  CircularProgress
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  RestartAlt as ResetIcon,
  Save as SaveIcon
} from '@mui/icons-material'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface WeightConfig {
  [key: string]: number
}

interface ReportConfig {
  energy_weights: WeightConfig
  price_optimization_weights: WeightConfig
  portfolio_decision_weights: WeightConfig
  confidence_threshold: number
  enable_fallback_options: boolean
  max_renewable_sources: number
}

interface ReportConfigPanelProps {
  config: ReportConfig
  isDefault: boolean
  onConfigChange: (config: ReportConfig) => void
  onSave: (config: ReportConfig) => Promise<void>
  onReset: () => void
}

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

const ReportConfigPanel: React.FC<ReportConfigPanelProps> = ({
  config,
  isDefault,
  onConfigChange,
  onSave,
  onReset
}) => {
  const [expanded, setExpanded] = useState(false)
  const [localConfig, setLocalConfig] = useState<ReportConfig>(config)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLocalConfig(config)
  }, [config])

  const handleWeightChange = (
    category: keyof ReportConfig,
    key: string,
    value: number
  ) => {
    const newConfig = { ...localConfig }
    ;(newConfig[category] as WeightConfig)[key] = value

    // Normalize weights to sum to 1.0
    const weights = newConfig[category] as WeightConfig
    const total = Object.values(weights).reduce((sum, w) => sum + w, 0)

    if (total > 0) {
      Object.keys(weights).forEach(k => {
        weights[k] = weights[k] / total
      })
    }

    setLocalConfig(newConfig)
    onConfigChange(newConfig)
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSaveSuccess(false)

    try {
      await onSave(localConfig)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    onReset()
    setSaveSuccess(false)
    setError(null)
  }

  const renderWeightSliders = (
    title: string,
    category: keyof ReportConfig,
    weights: WeightConfig,
    descriptions: { [key: string]: string }
  ) => {
    const chartData = Object.entries(weights).map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: value * 100
    }))

    return (
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {Object.entries(weights).map(([key, value]) => (
              <Box key={key} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(value * 100).toFixed(0)}%
                  </Typography>
                </Box>
                <Slider
                  value={value * 100}
                  onChange={(_, newValue) =>
                    handleWeightChange(category, key, (newValue as number) / 100)
                  }
                  min={0}
                  max={100}
                  step={5}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(v) => `${v}%`}
                />
                <Typography variant="caption" color="text.secondary">
                  {descriptions[key]}
                </Typography>
              </Box>
            ))}
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Weight Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `${value.toFixed(0)}%`} />
                <Legend
                  iconSize={10}
                  layout="horizontal"
                  verticalAlign="bottom"
                  wrapperStyle={{ fontSize: '11px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Grid>
        </Grid>
      </Box>
    )
  }

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h5">
              Report Configuration
            </Typography>
            {isDefault && (
              <Chip label="Using Defaults" size="small" color="info" />
            )}
          </Box>

          <IconButton onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {!expanded && (
          <Typography variant="body2" color="text.secondary">
            Click to customize report generation parameters and agent weights
          </Typography>
        )}

        <Collapse in={expanded}>
          <Box sx={{ mt: 3 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {saveSuccess && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Configuration saved successfully!
              </Alert>
            )}

            {/* Energy Source Weights */}
            {renderWeightSliders(
              '1. Energy Source Preferences',
              'energy_weights',
              localConfig.energy_weights,
              {
                solar: 'Preference for solar energy in the portfolio',
                wind: 'Preference for wind energy in the portfolio',
                hydro: 'Preference for hydroelectric energy in the portfolio'
              }
            )}

            <Divider sx={{ my: 3 }} />

            {/* Price Optimization Weights */}
            {renderWeightSliders(
              '2. Price Optimization Criteria',
              'price_optimization_weights',
              localConfig.price_optimization_weights,
              {
                cost: 'Weight given to minimizing total cost',
                reliability: 'Weight given to energy supply consistency',
                sustainability: 'Weight given to environmental impact'
              }
            )}

            <Divider sx={{ my: 3 }} />

            {/* Portfolio Decision Weights */}
            {renderWeightSliders(
              '3. Portfolio Decision Factors',
              'portfolio_decision_weights',
              localConfig.portfolio_decision_weights,
              {
                esg_score: 'Weight given to ESG and sustainability targets',
                budget_fit: 'Weight given to staying within budget',
                technical_feasibility: 'Weight given to implementation practicality'
              }
            )}

            <Divider sx={{ my: 3 }} />

            {/* Additional Settings */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Additional Settings
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Confidence Threshold
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Slider
                      value={localConfig.confidence_threshold}
                      onChange={(_, value) =>
                        setLocalConfig({ ...localConfig, confidence_threshold: value as number })
                      }
                      min={0}
                      max={1}
                      step={0.1}
                      valueLabelDisplay="auto"
                      marks
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="body2" fontWeight="bold" sx={{ minWidth: 40 }}>
                      {localConfig.confidence_threshold.toFixed(1)}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Minimum confidence required for recommendations
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Max Renewable Sources
                  </Typography>
                  <TextField
                    type="number"
                    value={localConfig.max_renewable_sources}
                    onChange={(e) =>
                      setLocalConfig({
                        ...localConfig,
                        max_renewable_sources: parseInt(e.target.value) || 4
                      })
                    }
                    inputProps={{ min: 1, max: 10 }}
                    fullWidth
                    size="small"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Maximum number of renewable sources in portfolio
                  </Typography>
                </Grid>
              </Grid>
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
              <Button
                startIcon={<ResetIcon />}
                onClick={handleReset}
                disabled={saving || isDefault}
              >
                Reset to Defaults
              </Button>

              <Button
                variant="contained"
                startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </Button>
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  )
}

export default ReportConfigPanel
