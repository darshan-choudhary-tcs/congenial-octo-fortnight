'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { sentimentAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useRouter } from 'next/navigation'
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Chip,
  LinearProgress,
  CircularProgress,
  Divider,
  AppBar,
  Toolbar,
  Container,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Grid,
  Alert,
  AlertTitle,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import {
  Home as HomeIcon,
  Upload as UploadIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Help as HelpIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`sentiment-tabpanel-${index}`}
      aria-labelledby={`sentiment-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

interface SentimentResult {
  id: number
  uuid: string
  input_type: string
  created_at: string
  completed_at?: string
  status: string
  original_filename?: string
  text_column?: string
  sentiment_column?: string
  confidence_column?: string
  results?: any
  total_rows?: number
  positive_count?: number
  negative_count?: number
  neutral_count?: number
  average_confidence?: number
  error_message?: string
}

export default function SentimentAnalysisPage() {
  const { user } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()

  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(false)

  // CSV Analysis State
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [columns, setColumns] = useState<string[]>([])
  const [textColumns, setTextColumns] = useState<string[]>([])
  const [selectedTextColumn, setSelectedTextColumn] = useState('')
  const [sentimentColumnName, setSentimentColumnName] = useState('sentiment')
  const [confidenceColumnName, setConfidenceColumnName] = useState('sentiment_confidence')

  // Results State
  const [results, setResults] = useState<SentimentResult[]>([])
  const [currentResult, setCurrentResult] = useState<SentimentResult | null>(null)

  useEffect(() => {
    if (!user) {
      router.push('/auth/login')
    } else {
      loadResults()
    }
  }, [user, router])

  const loadResults = async () => {
    try {
      const response = await sentimentAPI.getResults(20, 0)
      setResults(response.data)
    } catch (error: any) {
      console.error('Error loading results:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to load results', 'error')
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      showSnackbar('Please select a CSV file', 'error')
      return
    }

    setSelectedFile(file)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await sentimentAPI.getColumns(formData)
      const data = response.data

      setColumns(data.all_columns)
      setTextColumns(data.text_columns)

      if (data.text_columns.length > 0) {
        setSelectedTextColumn(data.text_columns[0])
      }

      showSnackbar('CSV file loaded successfully', 'success')
    } catch (error: any) {
      console.error('Error reading CSV:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to read CSV file', 'error')
      setSelectedFile(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeCSV = async () => {
    if (!selectedFile || !selectedTextColumn) {
      showSnackbar('Please select a file and text column', 'error')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('text_column', selectedTextColumn)
      formData.append('sentiment_column', sentimentColumnName)
      formData.append('confidence_column', confidenceColumnName)

      const response = await sentimentAPI.analyzeCSV(formData)
      const result = response.data

      showSnackbar('Sentiment analysis completed successfully!', 'success')
      setCurrentResult(result)
      setActiveTab(1) // Switch to results tab

      // Reload results list
      await loadResults()

      // Reset form
      setSelectedFile(null)
      setSelectedTextColumn('')
      setColumns([])
      setTextColumns([])
    } catch (error: any) {
      console.error('Error analyzing CSV:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to analyze CSV', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadResult = async (uuid: string, filename: string) => {
    try {
      const response = await sentimentAPI.exportResult(uuid)
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'sentiment_analysis.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      showSnackbar('CSV file downloaded successfully', 'success')
    } catch (error: any) {
      console.error('Error downloading result:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to download result', 'error')
    }
  }

  const handleDeleteResult = async (uuid: string) => {
    if (!confirm('Are you sure you want to delete this result?')) return

    try {
      await sentimentAPI.deleteResult(uuid)
      showSnackbar('Result deleted successfully', 'success')
      await loadResults()
      if (currentResult?.uuid === uuid) {
        setCurrentResult(null)
      }
    } catch (error: any) {
      console.error('Error deleting result:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to delete result', 'error')
    }
  }

  const handleViewResult = async (uuid: string) => {
    try {
      const response = await sentimentAPI.getResult(uuid)
      setCurrentResult(response.data)
      setActiveTab(1) // Switch to results tab
    } catch (error: any) {
      console.error('Error loading result:', error)
      showSnackbar(error.response?.data?.detail || 'Failed to load result', 'error')
    }
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return <TrendingUpIcon color="success" />
      case 'negative':
        return <TrendingDownIcon color="error" />
      case 'neutral':
        return <TrendingFlatIcon color="action" />
      default:
        return <InfoIcon />
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'success'
      case 'negative':
        return 'error'
      case 'neutral':
        return 'default'
      default:
        return 'default'
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => router.push('/dashboard')}
            sx={{ mr: 2 }}
          >
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Sentiment Analysis
          </Typography>
          <ThemeToggle />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ flexGrow: 1, py: 4, overflow: 'auto' }}>
        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
          >
            <Tab label="CSV Analysis" icon={<UploadIcon />} iconPosition="start" />
            <Tab label="Results" icon={<CheckCircleIcon />} iconPosition="start" />
            <Tab label="Help" icon={<HelpIcon />} iconPosition="start" />
          </Tabs>
        </Paper>

        {/* CSV Analysis Tab */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Upload CSV File
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Select a CSV file containing text data for sentiment analysis
                  </Typography>

                  <input
                    accept=".csv"
                    style={{ display: 'none' }}
                    id="csv-file-input"
                    type="file"
                    onChange={handleFileSelect}
                  />
                  <label htmlFor="csv-file-input">
                    <Button
                      variant="contained"
                      component="span"
                      startIcon={<UploadIcon />}
                      fullWidth
                      size="large"
                    >
                      Select CSV File
                    </Button>
                  </label>

                  {selectedFile && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      <AlertTitle>File Selected</AlertTitle>
                      {selectedFile.name}
                    </Alert>
                  )}

                  {loading && <LinearProgress sx={{ mt: 2 }} />}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Configuration
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Configure column names for analysis
                  </Typography>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Text Column</InputLabel>
                    <Select
                      value={selectedTextColumn}
                      label="Text Column"
                      onChange={(e) => setSelectedTextColumn(e.target.value)}
                      disabled={!selectedFile || textColumns.length === 0}
                    >
                      {textColumns.map((col) => (
                        <MenuItem key={col} value={col}>
                          {col}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    fullWidth
                    label="Sentiment Column Name"
                    value={sentimentColumnName}
                    onChange={(e) => setSentimentColumnName(e.target.value)}
                    sx={{ mb: 2 }}
                    helperText="Name for the output sentiment column"
                  />

                  <TextField
                    fullWidth
                    label="Confidence Column Name"
                    value={confidenceColumnName}
                    onChange={(e) => setConfidenceColumnName(e.target.value)}
                    sx={{ mb: 2 }}
                    helperText="Name for the output confidence score column"
                  />

                  <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    size="large"
                    onClick={handleAnalyzeCSV}
                    disabled={!selectedFile || !selectedTextColumn || loading}
                    startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                  >
                    {loading ? 'Analyzing...' : 'Analyze Sentiment'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {textColumns.length > 0 && (
              <Grid item xs={12}>
                <Alert severity="info">
                  <AlertTitle>Available Text Columns</AlertTitle>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                    {textColumns.map((col) => (
                      <Chip key={col} label={col} size="small" />
                    ))}
                  </Box>
                </Alert>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        {/* Results Tab */}
        <TabPanel value={activeTab} index={1}>
          {currentResult ? (
            <Box>
              <Paper sx={{ p: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h5">
                    {currentResult.original_filename || 'Analysis Result'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={() =>
                        handleDownloadResult(
                          currentResult.uuid,
                          `${currentResult.original_filename?.replace('.csv', '')}_sentiment.csv`
                        )
                      }
                    >
                      Download CSV
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setCurrentResult(null)}
                    >
                      Back to List
                    </Button>
                  </Box>
                </Box>

                {currentResult.status === 'completed' && (
                  <>
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      <Grid item xs={12} sm={6} md={3}>
                        <Card>
                          <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                              Total Rows
                            </Typography>
                            <Typography variant="h4">
                              {currentResult.total_rows?.toLocaleString()}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <Card sx={{ bgcolor: 'success.light' }}>
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <TrendingUpIcon />
                              <Typography color="text.secondary">
                                Positive
                              </Typography>
                            </Box>
                            <Typography variant="h4">
                              {currentResult.positive_count?.toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              {currentResult.total_rows &&
                                `${((currentResult.positive_count! / currentResult.total_rows) * 100).toFixed(1)}%`}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <Card sx={{ bgcolor: 'error.light' }}>
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <TrendingDownIcon />
                              <Typography color="text.secondary">
                                Negative
                              </Typography>
                            </Box>
                            <Typography variant="h4">
                              {currentResult.negative_count?.toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              {currentResult.total_rows &&
                                `${((currentResult.negative_count! / currentResult.total_rows) * 100).toFixed(1)}%`}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>

                      <Grid item xs={12} sm={6} md={3}>
                        <Card sx={{ bgcolor: 'action.hover' }}>
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <TrendingFlatIcon />
                              <Typography color="text.secondary">
                                Neutral
                              </Typography>
                            </Box>
                            <Typography variant="h4">
                              {currentResult.neutral_count?.toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              {currentResult.total_rows &&
                                `${((currentResult.neutral_count! / currentResult.total_rows) * 100).toFixed(1)}%`}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>

                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                              Average Confidence Score
                            </Typography>
                            <Typography variant="h4">
                              {(currentResult.average_confidence! * 100).toFixed(1)}%
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    <Alert severity="success">
                      <AlertTitle>Analysis Complete</AlertTitle>
                      Analyzed {currentResult.total_rows} rows from column &quot;{currentResult.text_column}&quot;.
                      Results saved to columns &quot;{currentResult.sentiment_column}&quot; and &quot;{currentResult.confidence_column}&quot;.
                    </Alert>
                  </>
                )}

                {currentResult.status === 'failed' && (
                  <Alert severity="error">
                    <AlertTitle>Analysis Failed</AlertTitle>
                    {currentResult.error_message}
                  </Alert>
                )}
              </Paper>
            </Box>
          ) : (
            <Box>
              <Typography variant="h6" gutterBottom>
                Analysis History
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Filename</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Total Rows</TableCell>
                      <TableCell>Positive</TableCell>
                      <TableCell>Negative</TableCell>
                      <TableCell>Neutral</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {results.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} align="center">
                          <Typography color="text.secondary" sx={{ py: 4 }}>
                            No analysis results yet. Upload a CSV file to get started.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      results.map((result) => (
                        <TableRow key={result.uuid} hover>
                          <TableCell>{result.original_filename || 'N/A'}</TableCell>
                          <TableCell>
                            {new Date(result.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={result.status}
                              color={result.status === 'completed' ? 'success' : result.status === 'failed' ? 'error' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{result.total_rows?.toLocaleString() || '-'}</TableCell>
                          <TableCell>
                            <Chip
                              icon={<TrendingUpIcon />}
                              label={result.positive_count || 0}
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              icon={<TrendingDownIcon />}
                              label={result.negative_count || 0}
                              size="small"
                              color="error"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              icon={<TrendingFlatIcon />}
                              label={result.neutral_count || 0}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                              <IconButton
                                size="small"
                                onClick={() => handleViewResult(result.uuid)}
                                title="View Details"
                              >
                                <InfoIcon />
                              </IconButton>
                              {result.status === 'completed' && (
                                <IconButton
                                  size="small"
                                  onClick={() =>
                                    handleDownloadResult(
                                      result.uuid,
                                      `${result.original_filename?.replace('.csv', '')}_sentiment.csv`
                                    )
                                  }
                                  title="Download"
                                >
                                  <DownloadIcon />
                                </IconButton>
                              )}
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteResult(result.uuid)}
                                title="Delete"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </TabPanel>

        {/* Help Tab */}
        <TabPanel value={activeTab} index={2}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
              Sentiment Analysis Help
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Overview</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography paragraph>
                  The Sentiment Analysis feature uses a Support Vector Machine (SVM) classifier to analyze
                  the emotional tone of text data. It classifies text into three categories:
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TrendingUpIcon color="success" />
                    <Typography><strong>Positive:</strong> Text expressing favorable, happy, or optimistic sentiment</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TrendingDownIcon color="error" />
                    <Typography><strong>Negative:</strong> Text expressing unfavorable, sad, or pessimistic sentiment</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <TrendingFlatIcon color="action" />
                    <Typography><strong>Neutral:</strong> Text that is objective or lacks strong emotional tone</Typography>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Workflow</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="h6" gutterBottom>
                  Step 1: Prepare Your CSV File
                </Typography>
                <Typography paragraph>
                  Ensure your CSV file contains at least one column with text data. The text can be:
                </Typography>
                <Box component="ul" sx={{ mb: 2 }}>
                  <li>Customer reviews or feedback</li>
                  <li>Social media posts or comments</li>
                  <li>Survey responses</li>
                  <li>Product descriptions</li>
                  <li>Any text data you want to analyze</li>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Step 2: Upload and Configure
                </Typography>
                <Box component="ol" sx={{ mb: 2 }}>
                  <li>Click &quot;Select CSV File&quot; in the CSV Analysis tab</li>
                  <li>The system will automatically detect text columns in your file</li>
                  <li>Select which column contains the text you want to analyze</li>
                  <li>Optionally customize the output column names (default: &quot;sentiment&quot; and &quot;sentiment_confidence&quot;)</li>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Step 3: Run Analysis
                </Typography>
                <Typography paragraph>
                  Click &quot;Analyze Sentiment&quot; to process your file. The system will:
                </Typography>
                <Box component="ul" sx={{ mb: 2 }}>
                  <li>Read your CSV file</li>
                  <li>Preprocess the text (lowercase, remove special characters, etc.)</li>
                  <li>Apply the pre-trained SVM model to classify each row</li>
                  <li>Generate confidence scores (0-1) for each prediction</li>
                  <li>Create a new CSV with the original data plus sentiment columns</li>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Step 4: View Results and Download
                </Typography>
                <Typography paragraph>
                  After analysis completes, you&apos;ll see:
                </Typography>
                <Box component="ul" sx={{ mb: 2 }}>
                  <li>Summary statistics showing distribution of sentiments</li>
                  <li>Average confidence score</li>
                  <li>Download button to get the updated CSV file</li>
                  <li>All previous analyses in the Results tab</li>
                </Box>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Technical Details</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="h6" gutterBottom>
                  Machine Learning Model
                </Typography>
                <Typography paragraph>
                  This feature uses a <strong>Support Vector Machine (SVM)</strong> classifier with:
                </Typography>
                <Box component="ul" sx={{ mb: 2 }}>
                  <li><strong>TF-IDF Vectorization:</strong> Converts text to numerical features</li>
                  <li><strong>LinearSVC:</strong> Linear kernel for efficient multi-class classification</li>
                  <li><strong>Class Balancing:</strong> Handles imbalanced datasets automatically</li>
                  <li><strong>Preprocessing:</strong> URL removal, special character handling, lowercasing</li>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Confidence Scores
                </Typography>
                <Typography paragraph>
                  Each prediction includes a confidence score (0-1) indicating the model&apos;s certainty:
                </Typography>
                <Box component="ul" sx={{ mb: 2 }}>
                  <li><strong>0.8-1.0:</strong> High confidence</li>
                  <li><strong>0.6-0.8:</strong> Medium confidence</li>
                  <li><strong>0.0-0.6:</strong> Low confidence (manual review recommended)</li>
                </Box>

                <Typography variant="h6" gutterBottom>
                  Use Cases
                </Typography>
                <Box component="ul">
                  <li>Customer feedback analysis</li>
                  <li>Social media monitoring</li>
                  <li>Product review sentiment tracking</li>
                  <li>Survey response analysis</li>
                  <li>Brand reputation monitoring</li>
                  <li>Market research and trend analysis</li>
                </Box>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Best Practices</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box component="ul">
                  <li>Ensure text data is in English (model is trained on English text)</li>
                  <li>Longer text generally produces more accurate results</li>
                  <li>Review low-confidence predictions manually for critical applications</li>
                  <li>The model works best with clear, well-formed sentences</li>
                  <li>Very short text (1-2 words) may not provide reliable results</li>
                  <li>Keep original data for reference - the system adds new columns without removing old ones</li>
                </Box>
              </AccordionDetails>
            </Accordion>

            <Alert severity="info" sx={{ mt: 3 }}>
              <AlertTitle>Pre-trained Model</AlertTitle>
              This feature uses a pre-trained SVM model that has been initialized with general sentiment examples.
              The model is designed to be generic and reusable across various text analysis use cases.
            </Alert>
          </Paper>
        </TabPanel>
      </Container>
    </Box>
  )
}
