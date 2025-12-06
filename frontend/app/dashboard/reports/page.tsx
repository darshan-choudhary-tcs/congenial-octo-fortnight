'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { reportsAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import ReportConfigPanel from '@/components/ReportConfigPanel'
import { useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  Box,
  Button,
  Paper,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stepper,
  Step,
  StepLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  AppBar,
  Toolbar,
  IconButton,
  Tooltip as MuiTooltip,
  Stack,
} from '@mui/material'
import {
  Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayArrowIcon,
  Home as HomeIcon,
  WbSunny as SolarIcon,
  Air as WindIcon,
  Water as HydroIcon,
  Grass as BiomassIcon,
  TrendingUp as TrendingUpIcon,
  MonetizationOn as MoneyIcon,
  Recycling as EcoIcon,
  Logout as LogOutIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const ENERGY_COLORS = {
  solar: '#f59e0b',
  wind: '#0ea5e9',
  hydro: '#10b981',
  biomass: '#84cc16',
}

const CONFIDENCE_COLORS = {
  high: '#10b981',
  medium: '#f59e0b',
  low: '#ef4444',
}

// Helper component for rendering markdown content with MUI styling
const MarkdownContent = ({ content }: { content: string }) => (
  <Box
    sx={{
      '& p': { mb: 1.5, lineHeight: 1.8 },
      '& ul, & ol': { pl: 2, mb: 1.5 },
      '& li': { mb: 0.5 },
      '& h1, & h2, & h3': { mt: 2, mb: 1, fontWeight: 'bold' },
      '& h1': { fontSize: '1.5rem' },
      '& h2': { fontSize: '1.25rem' },
      '& h3': { fontSize: '1.1rem' },
      '& code': {
        bgcolor: 'grey.100',
        px: 0.5,
        py: 0.25,
        borderRadius: 0.5,
        fontSize: '0.875rem',
        fontFamily: 'monospace'
      },
      '& pre': {
        bgcolor: 'grey.100',
        p: 1.5,
        borderRadius: 1,
        overflow: 'auto',
        mb: 1.5
      },
      '& blockquote': {
        borderLeft: '3px solid',
        borderColor: 'primary.main',
        pl: 2,
        py: 0.5,
        my: 1.5,
        color: 'text.secondary',
        fontStyle: 'italic'
      },
      '& strong': { fontWeight: 600 },
      '& em': { fontStyle: 'italic' },
      '& table': { borderCollapse: 'collapse', width: '100%', mb: 1.5 },
      '& th, & td': { border: '1px solid', borderColor: 'divider', p: 1 },
      '& th': { bgcolor: 'grey.100', fontWeight: 'bold' },
    }}
  >
    <ReactMarkdown>{content}</ReactMarkdown>
  </Box>
)

// Helper component for rendering source citations with tooltips
const SourceCitation = ({ source, index }: { source: any; index: number }) => (
  <MuiTooltip
    title={
      <Box sx={{ p: 0.5 }}>
        <Typography variant="caption" fontWeight="bold" display="block" gutterBottom>
          {source.metadata?.filename || `Document ${index + 1}`}
        </Typography>
        <Typography variant="caption" display="block">
          Relevance: {(source.similarity * 100).toFixed(1)}%
        </Typography>
        {source.metadata?.page && (
          <Typography variant="caption" display="block">
            Page: {source.metadata.page}
          </Typography>
        )}
        {source.metadata?.chunk_id !== undefined && (
          <Typography variant="caption" display="block">
            Chunk: {source.metadata.chunk_id}
          </Typography>
        )}
      </Box>
    }
    arrow
    placement="top"
  >
    <Chip
      label={`[${index + 1}]`}
      size="small"
      sx={{
        cursor: 'pointer',
        mx: 0.5,
        height: 20,
        fontSize: '0.7rem',
        bgcolor: 'primary.main',
        color: 'white',
        '&:hover': {
          bgcolor: 'primary.dark',
        },
      }}
    />
  </MuiTooltip>
)

interface ReportConfig {
  energy_weights: { [key: string]: number }
  price_optimization_weights: { [key: string]: number }
  portfolio_decision_weights: { [key: string]: number }
  confidence_threshold: number
  enable_fallback_options: boolean
  max_renewable_sources: number
}

interface AgentResult {
  agent: string
  status: string
  confidence: number
  reasoning: string
  data: any
}

interface ReportSection {
  renewable_options?: any[]
  optimized_mix?: any[]
  portfolio?: any
  analysis?: string
  confidence?: number
  reasoning?: string
  sources?: any[]
}

export default function ReportsPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()

  const [config, setConfig] = useState<ReportConfig | null>(null)
  const [isDefault, setIsDefault] = useState(true)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [report, setReport] = useState<any>(null)
  const [reportStatus, setReportStatus] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportingClientside, setExportingClientside] = useState(false)
  const [savedReportId, setSavedReportId] = useState<number | null>(null)

  const agentSteps = [
    'Energy Availability Analysis',
    'Price Optimization',
    'Portfolio Decision',
  ]

  useEffect(() => {
    loadConfig()
    checkReportStatus()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await reportsAPI.getConfig()
      setConfig(response.data.config)
      setIsDefault(response.data.is_default)
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to load configuration', 'error')
    } finally {
      setLoading(false)
    }
  }

  const checkReportStatus = async () => {
    try {
      const response = await reportsAPI.getStatus()
      setReportStatus(response.data)
    } catch (error) {
      console.error('Failed to check report status:', error)
    }
  }

  const handleSaveConfig = async (newConfig: ReportConfig) => {
    const response = await reportsAPI.updateConfig(newConfig)
    setConfig(response.data.config)
    setIsDefault(response.data.is_default)
    showSnackbar('Configuration saved successfully', 'success')
  }

  const handleResetConfig = async () => {
    await loadConfig()
    showSnackbar('Configuration reset to defaults', 'info')
  }

  const generateReport = async () => {
    // if (!reportStatus?.ready) {
    //   showSnackbar('Please complete your profile setup first', 'warning')
    //   return
    // }

    setGenerating(true)
    setCurrentStep(0)
    setReport(null)

    try {
      const response = await reportsAPI.generateReport({
        provider: user?.preferred_llm || 'custom',
      })

      setReport(response.data)
      setCurrentStep(3)
      setSavedReportId(null) // Reset saved report ID for new report
      showSnackbar('Report generated successfully!', 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to generate report', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const handleSaveReport = async () => {
    if (!report) return

    setSaving(true)
    try {
      // Prepare profile snapshot from reportStatus
      const profileSnapshot = {
        industry: reportStatus?.profile?.industry || 'N/A',
        location: reportStatus?.profile?.location || 'N/A',
        budget: reportStatus?.profile?.budget || 0,
        sustainability_target_kp1: reportStatus?.profile?.sustainability_target_kp1 || 2030,
        sustainability_target_kp2: reportStatus?.profile?.sustainability_target_kp2 || 50,
        company: user?.company || 'N/A',
      }

      // Prepare config snapshot
      const configSnapshot = config || {}

      // Calculate total tokens (if available in report)
      const totalTokens = report.report_sections?.availability_agent?.metadata?.total_tokens || 0

      const response = await reportsAPI.saveReport({
        report_name: `Energy Report - ${new Date().toLocaleDateString()}`,
        report_content: {
          availability_agent: report.report_sections?.availability_agent || {},
          optimization_agent: report.report_sections?.optimization_agent || {},
          portfolio_agent: report.report_sections?.portfolio_agent || {},
          overall_confidence: report.overall_confidence,
          reasoning_chain: report.reasoning_chain || [],
          execution_metadata: {
            execution_time: report.execution_time,
            agents_involved: report.agents_involved,
          },
        },
        profile_snapshot: profileSnapshot,
        config_snapshot: configSnapshot,
        overall_confidence: report.overall_confidence,
        execution_time: report.execution_time,
        total_tokens: totalTokens,
      })

      setSavedReportId(response.data.report_id)
      showSnackbar('Report saved successfully!', 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save report', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleExportPDF = async () => {
    if (!savedReportId) {
      showSnackbar('Please save the report first before exporting', 'warning')
      return
    }

    setExporting(true)
    try {
      // Fetch the saved report data
      const response = await reportsAPI.getSavedReport(savedReportId)
      const reportData = response.data

      // Dynamically import PDF generator
      const { generateReportPDF } = await import('@/lib/pdfGenerator')

      // Generate PDF on client side
      generateReportPDF(reportData)

      showSnackbar('PDF exported successfully!', 'success')
    } catch (error: any) {
      showSnackbar('Failed to export PDF', 'error')
    } finally {
      setExporting(false)
    }
  }

  const handleExportClientsidePDF = async () => {
    if (!report) {
      showSnackbar('No report available to export', 'warning')
      return
    }

    setExportingClientside(true)
    try {
      // Dynamically import PDF generator
      const { generateReportPDF } = await import('@/lib/pdfGenerator')

      // Create a report structure similar to saved reports
      const reportData = {
        id: 0, // Temporary ID for unsaved report
        report_name: `Energy Portfolio Report - ${new Date().toLocaleDateString()}`,
        report_type: 'energy_portfolio',
        report_content: report,
        profile_snapshot: null,
        config_snapshot: config,
        overall_confidence: report.overall_confidence,
        execution_time: report.execution_time,
        total_tokens: report.total_tokens_used || 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Generate PDF on client side
      generateReportPDF(reportData)

      showSnackbar('PDF exported successfully!', 'success')
    } catch (error: any) {
      showSnackbar('Failed to export PDF', 'error')
    } finally {
      setExportingClientside(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return CONFIDENCE_COLORS.high
    if (confidence >= 0.4) return CONFIDENCE_COLORS.medium
    return CONFIDENCE_COLORS.low
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.7) return 'High Confidence'
    if (confidence >= 0.4) return 'Medium Confidence'
    return 'Low Confidence'
  }

  const renderEnergyMixChart = (data: any[]) => {
    if (!data || data.length === 0) return null

    const chartData = data.map((item) => ({
      name: item.source || item.type,
      value: item.percentage || 0,
      cost: item.annual_cost || 0,
    }))

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={ENERGY_COLORS[entry.name.toLowerCase() as keyof typeof ENERGY_COLORS] || '#8884d8'}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  const renderCostChart = (data: any[]) => {
    if (!data || data.length === 0) return null

    const chartData = data.map((item) => ({
      name: item.source || item.type,
      cost: item.annual_cost || 0,
      costPerKwh: item.cost_per_kwh || 0,
    }))

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip formatter={(value: number) => `₹${value.toLocaleString()}`} />
          <Legend />
          <Bar dataKey="cost" fill="#2563eb" name="Annual Cost (₹)" />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  const renderTransitionRoadmap = (roadmap: any[]) => {
    if (!roadmap || roadmap.length === 0) return null

    const chartData = roadmap.map((item) => ({
      year: item.year,
      renewable: item.renewable_percentage,
    }))

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis domain={[0, 100]} />
          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
          <Legend />
          <Line
            type="monotone"
            dataKey="renewable"
            stroke="#10b981"
            strokeWidth={3}
            name="Renewable Energy %"
            dot={{ fill: '#10b981', r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button
                variant="text"
                startIcon={<HomeIcon />}
                onClick={() => router.push('/dashboard')}
              >
                Dashboard
              </Button>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  Energy Reports
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <ThemeToggle />
              <Chip
                label={user?.full_name || user?.username}
                color="primary"
                size="small"
              />
            </Box>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {reportStatus?.warnings && reportStatus.warnings.length > 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            {reportStatus.warnings.map((warning: string, index: number) => (
              <Typography key={index} variant="body2">
                • {warning}
              </Typography>
            ))}
          </Alert>
        )}

        {/* Configuration Panel */}
        {config && (
          <ReportConfigPanel
            config={config}
            isDefault={isDefault}
            onConfigChange={setConfig}
            onSave={handleSaveConfig}
            onReset={handleResetConfig}
          />
        )}

        {/* Generate Report Button */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Generate Energy Analysis Report
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Multi-agent system will analyze renewable energy options, optimize pricing, and create a portfolio recommendation.
              </Typography>
            </Box>
            <Button
              variant="contained"
              size="large"
              startIcon={generating ? <CircularProgress size={20} /> : <PlayArrowIcon />}
              onClick={generateReport}
              // disabled={generating || !reportStatus?.ready}
            >
              {generating ? 'Generating...' : 'Generate Report'}
            </Button>
          </Box>

          {/* Progress Stepper */}
          {generating && (
            <Box sx={{ mt: 3 }}>
              <Stepper activeStep={currentStep} alternativeLabel>
                {agentSteps.map((label, index) => (
                  <Step key={label}>
                    <StepLabel
                      StepIconComponent={() => (
                        currentStep > index ? (
                          <CheckCircleIcon sx={{ color: '#10b981', fontSize: 32 }} />
                        ) : currentStep === index ? (
                          <CircularProgress size={24} />
                        ) : (
                          <Box sx={{ width: 24, height: 24, borderRadius: '50%', bgcolor: 'grey.300' }} />
                        )
                      )}
                    >
                      {label}
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>
            </Box>
          )}
        </Paper>

        {/* Report Results */}
        {report && (
          <>
            {/* Overall Summary */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5">
                  Report Summary
                </Typography>
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSaveReport}
                    disabled={saving || savedReportId !== null}
                    startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                  >
                    {savedReportId ? 'Saved' : saving ? 'Saving...' : 'Save Report'}
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    onClick={handleExportPDF}
                    disabled={exporting || !savedReportId}
                    startIcon={exporting ? <CircularProgress size={20} /> : <DownloadIcon />}
                  >
                    {exporting ? 'Exporting...' : 'Export PDF'}
                  </Button>
                  <Button
                    variant="outlined"
                    color="success"
                    onClick={handleExportClientsidePDF}
                    disabled={exportingClientside}
                    startIcon={exportingClientside ? <CircularProgress size={20} /> : <DownloadIcon />}
                  >
                    {exportingClientside ? 'Exporting...' : 'Export (clientside)'}
                  </Button>
                </Stack>
              </Box>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Overall Confidence
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="h4">
                          {(report.overall_confidence * 100).toFixed(0)}%
                        </Typography>
                        <Chip
                          label={getConfidenceLabel(report.overall_confidence)}
                          size="small"
                          sx={{
                            bgcolor: getConfidenceColor(report.overall_confidence),
                            color: 'white',
                          }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Execution Time
                      </Typography>
                      <Typography variant="h4">{report.execution_time?.toFixed(1)}s</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Agents Involved
                      </Typography>
                      <Typography variant="h4">{report.agents_involved?.length || 3}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Provider
                      </Typography>
                      <Typography variant="h4" sx={{ textTransform: 'capitalize' }}>
                        {report.provider || 'Custom'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>

            {/* Agent Results */}
            <Grid container spacing={3}>
              {/* Energy Availability Agent */}
              <Grid item xs={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <SolarIcon sx={{ mr: 1, color: '#f59e0b' }} />
                      <Typography variant="h6">Energy Availability</Typography>
                    </Box>
                    <Chip
                      label={`Confidence: ${(report.report_sections.energy_availability?.confidence * 100 || 0).toFixed(0)}%`}
                      size="small"
                      sx={{
                        bgcolor: getConfidenceColor(report.report_sections.energy_availability?.confidence || 0),
                        color: 'white',
                        mb: 2,
                      }}
                    />

                    {report.report_sections.energy_availability?.renewable_options && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          Available Sources:
                        </Typography>
                        <List dense>
                          {report.report_sections.energy_availability.renewable_options.map((option: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={option.type || option.source}
                                secondary={`Reliability: ${((option.reliability_score || 0) * 100).toFixed(0)}%`}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          <TrendingUpIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                          <Typography variant="body2" fontWeight="medium">View Detailed Analysis & Reasoning</Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="bold" color="primary" gutterBottom>
                            Agent Analysis:
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                            {report.report_sections.energy_availability?.reasoning}
                          </Typography>

                          {report.report_sections.energy_availability?.analysis && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, borderLeft: '3px solid', borderColor: 'primary.main' }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Full Technical Analysis:
                              </Typography>
                              <Box sx={{ color: 'text.secondary' }}>
                                <MarkdownContent content={report.report_sections.energy_availability.analysis} />
                              </Box>
                            </Box>
                          )}

                          {report.report_sections.energy_availability?.sources && report.report_sections.energy_availability.sources.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Data Sources ({report.report_sections.energy_availability.sources.length}):
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                {report.report_sections.energy_availability.sources.map((source: any, idx: number) => (
                                  <SourceCitation key={idx} source={source} index={idx} />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>

              {/* Price Optimization Agent */}
              <Grid item xs={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <MoneyIcon sx={{ mr: 1, color: '#10b981' }} />
                      <Typography variant="h6">Price Optimization</Typography>
                    </Box>
                    <Chip
                      label={`Confidence: ${(report.report_sections.price_optimization?.confidence * 100 || 0).toFixed(0)}%`}
                      size="small"
                      sx={{
                        bgcolor: getConfidenceColor(report.report_sections.price_optimization?.confidence || 0),
                        color: 'white',
                        mb: 2,
                      }}
                    />

                    {report.report_sections.price_optimization?.optimized_mix && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          Optimized Mix:
                        </Typography>
                        {renderEnergyMixChart(report.report_sections.price_optimization.optimized_mix)}
                      </Box>
                    )}

                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          <MoneyIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                          <Typography variant="body2" fontWeight="medium">View Detailed Analysis & Reasoning</Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="bold" color="primary" gutterBottom>
                            Optimization Strategy:
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                            {report.report_sections.price_optimization?.reasoning}
                          </Typography>

                          {report.report_sections.price_optimization?.analysis && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, borderLeft: '3px solid', borderColor: 'success.main' }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                💰 Detailed Cost-Benefit Analysis:
                              </Typography>
                              <Box sx={{ color: 'text.secondary' }}>
                                <MarkdownContent content={report.report_sections.price_optimization.analysis} />
                              </Box>
                            </Box>
                          )}

                          {report.report_sections.price_optimization?.metadata && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                📈 Key Metrics:
                              </Typography>
                              <Grid container spacing={1}>
                                {report.report_sections.price_optimization.metadata.budget && (
                                  <Grid item xs={6}>
                                    <Typography variant="caption" color="text.secondary">Budget:</Typography>
                                    <Typography variant="body2" fontWeight="bold">₹{report.report_sections.price_optimization.metadata.budget.toLocaleString()}</Typography>
                                  </Grid>
                                )}
                                {report.report_sections.price_optimization.metadata.total_cost && (
                                  <Grid item xs={6}>
                                    <Typography variant="caption" color="text.secondary">Total Cost:</Typography>
                                    <Typography variant="body2" fontWeight="bold">₹{report.report_sections.price_optimization.metadata.total_cost.toLocaleString()}</Typography>
                                  </Grid>
                                )}
                                {report.report_sections.price_optimization.metadata.sources_analyzed && (
                                  <Grid item xs={6}>
                                    <Typography variant="caption" color="text.secondary">Sources Analyzed:</Typography>
                                    <Typography variant="body2" fontWeight="bold">{report.report_sections.price_optimization.metadata.sources_analyzed}</Typography>
                                  </Grid>
                                )}
                              </Grid>
                            </Box>
                          )}

                          {report.report_sections.price_optimization?.sources && report.report_sections.price_optimization.sources.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Data Sources ({report.report_sections.price_optimization.sources.length}):
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                {report.report_sections.price_optimization.sources.map((source: any, idx: number) => (
                                  <SourceCitation key={idx} source={source} index={idx} />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>

              {/* Portfolio Decision Agent */}
              <Grid item xs={12} lg={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <EcoIcon sx={{ mr: 1, color: '#10b981' }} />
                      <Typography variant="h6">Portfolio Decision</Typography>
                    </Box>
                    <Chip
                      label={`Confidence: ${(report.report_sections.portfolio_decision?.confidence * 100 || 0).toFixed(0)}%`}
                      size="small"
                      sx={{
                        bgcolor: getConfidenceColor(report.report_sections.portfolio_decision?.confidence || 0),
                        color: 'white',
                        mb: 2,
                      }}
                    />

                    {report.report_sections.portfolio_decision?.portfolio?.esg_scores && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          ESG Scores:
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText
                              primary={`Renewable: ${report.report_sections.portfolio_decision.portfolio.esg_scores.renewable_percentage.toFixed(1)}%`}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary={`Sustainability Score: ${report.report_sections.portfolio_decision.portfolio.esg_scores.sustainability_score.toFixed(0)}/100`}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary={`Target Met: ${report.report_sections.portfolio_decision.portfolio.meets_targets ? 'Yes' : 'No'}`}
                            />
                          </ListItem>
                        </List>
                      </Box>
                    )}

                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          <EcoIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                          <Typography variant="body2" fontWeight="medium">View Detailed Analysis & Reasoning</Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="bold" color="primary" gutterBottom>
                            Portfolio Decision Rationale:
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                            {report.report_sections.portfolio_decision?.reasoning}
                          </Typography>

                          {report.report_sections.portfolio_decision?.analysis && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, borderLeft: '3px solid', borderColor: 'success.main' }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                🌱 ESG & Sustainability Analysis:
                              </Typography>
                              <Box sx={{ color: 'text.secondary' }}>
                                <MarkdownContent content={report.report_sections.portfolio_decision.analysis} />
                              </Box>
                            </Box>
                          )}

                          {report.report_sections.portfolio_decision?.portfolio?.esg_scores && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                🎯 ESG Performance Indicators:
                              </Typography>
                              <Grid container spacing={1}>
                                {Object.entries(report.report_sections.portfolio_decision.portfolio.esg_scores).map(([key, value]: [string, any]) => (
                                  <Grid item xs={6} key={key}>
                                    <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                                      {key.replace(/_/g, ' ')}:
                                    </Typography>
                                    <Typography variant="body2" fontWeight="bold">
                                      {typeof value === 'number' ? `${value.toFixed(1)}${key.includes('percentage') ? '%' : ''}` : value}
                                    </Typography>
                                  </Grid>
                                ))}
                              </Grid>
                            </Box>
                          )}

                          {report.report_sections.portfolio_decision?.metadata && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                📊 Decision Parameters:
                              </Typography>
                              <List dense>
                                {report.report_sections.portfolio_decision.metadata.sustainability_target_kp1 && (
                                  <ListItem sx={{ py: 0.5 }}>
                                    <ListItemText
                                      primary="Target Year (KP1)"
                                      secondary={report.report_sections.portfolio_decision.metadata.sustainability_target_kp1}
                                      primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
                                      secondaryTypographyProps={{ variant: 'caption' }}
                                    />
                                  </ListItem>
                                )}
                                {report.report_sections.portfolio_decision.metadata.sustainability_target_kp2 && (
                                  <ListItem sx={{ py: 0.5 }}>
                                    <ListItemText
                                      primary="Target Renewable % (KP2)"
                                      secondary={`${report.report_sections.portfolio_decision.metadata.sustainability_target_kp2}%`}
                                      primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
                                      secondaryTypographyProps={{ variant: 'caption' }}
                                    />
                                  </ListItem>
                                )}
                                {report.report_sections.portfolio_decision.metadata.current_renewable_percentage !== undefined && (
                                  <ListItem sx={{ py: 0.5 }}>
                                    <ListItemText
                                      primary="Current Renewable %"
                                      secondary={`${report.report_sections.portfolio_decision.metadata.current_renewable_percentage.toFixed(1)}%`}
                                      primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
                                      secondaryTypographyProps={{ variant: 'caption' }}
                                    />
                                  </ListItem>
                                )}
                              </List>
                            </Box>
                          )}

                          {report.report_sections.portfolio_decision?.sources && report.report_sections.portfolio_decision.sources.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Data Sources ({report.report_sections.portfolio_decision.sources.length}):
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                {report.report_sections.portfolio_decision.sources.map((source: any, idx: number) => (
                                  <SourceCitation key={idx} source={source} index={idx} />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Detailed Visualizations */}
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h5" gutterBottom>
                Detailed Analysis
              </Typography>

              <Grid container spacing={3} sx={{ mt: 1 }}>
                {/* Energy Mix */}
                {report.report_sections.price_optimization?.optimized_mix && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Energy Portfolio Mix
                    </Typography>
                    {renderEnergyMixChart(report.report_sections.price_optimization.optimized_mix)}
                  </Grid>
                )}

                {/* Cost Breakdown */}
                {report.report_sections.price_optimization?.optimized_mix && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Cost Breakdown
                    </Typography>
                    {renderCostChart(report.report_sections.price_optimization.optimized_mix)}
                  </Grid>
                )}

                {/* Transition Roadmap */}
                {report.report_sections.portfolio_decision?.portfolio?.transition_roadmap && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Transition Roadmap to Net Zero
                    </Typography>
                    {renderTransitionRoadmap(report.report_sections.portfolio_decision.portfolio.transition_roadmap)}
                  </Grid>
                )}
              </Grid>
            </Paper>

            {/* Reasoning Chain */}
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h5" gutterBottom>
                Reasoning Chain
              </Typography>
              <List>
                {report.reasoning_chain?.map((step: any, index: number) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={`Step ${step.step}: ${step.action}`}
                      secondary={
                        <>
                          <Typography variant="body2" color="text.secondary">
                            {step.description}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Outcome: {step.outcome}
                          </Typography>
                          <Chip
                            label={`Confidence: ${(step.confidence * 100).toFixed(0)}%`}
                            size="small"
                            sx={{
                              mt: 1,
                              bgcolor: getConfidenceColor(step.confidence),
                              color: 'white',
                            }}
                          />
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </>
        )}
      </Container>
    </Box>
  )
}
