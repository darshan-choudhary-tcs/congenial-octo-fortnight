'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { reportsAPI } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { useRouter } from 'next/navigation'
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
  CircularProgress,
  Alert,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  TextField,
  InputAdornment,
} from '@mui/material'
import {
  Home as HomeIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  Chat as ChatIcon,
} from '@mui/icons-material'

interface SavedReportSummary {
  id: number
  report_name: string | null
  report_type: string
  overall_confidence: number
  execution_time: number
  created_at: string
  industry: string
  location: string
}

export default function SavedReportsPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()

  const [reports, setReports] = useState<SavedReportSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [deleteDialog, setDeleteDialog] = useState<number | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedReport, setSelectedReport] = useState<any>(null)
  const [viewDialog, setViewDialog] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      setLoading(true)
      const response = await reportsAPI.getSavedReports()
      setReports(response.data)
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to load saved reports', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleExportPDF = async (reportId: number) => {
    setExporting(reportId)
    try {
      // Fetch the saved report data
      const response = await reportsAPI.getSavedReport(reportId)
      const reportData = response.data

      // Dynamically import PDF generator
      const { generateReportPDF } = await import('@/lib/pdfGenerator')

      // Generate PDF on client side
      generateReportPDF(reportData)

      showSnackbar('PDF exported successfully!', 'success')
    } catch (error: any) {
      showSnackbar('Failed to export PDF', 'error')
    } finally {
      setExporting(null)
    }
  }

  const handleDeleteReport = async (reportId: number) => {
    setDeleting(reportId)
    try {
      await reportsAPI.deleteSavedReport(reportId)
      setReports(reports.filter(r => r.id !== reportId))
      setDeleteDialog(null)
      showSnackbar('Report deleted successfully!', 'success')
    } catch (error: any) {
      showSnackbar('Failed to delete report', 'error')
    } finally {
      setDeleting(null)
    }
  }

  const handleViewReport = async (reportId: number) => {
    setLoadingDetail(true)
    setViewDialog(true)
    try {
      const response = await reportsAPI.getSavedReport(reportId)
      setSelectedReport(response.data)
    } catch (error: any) {
      showSnackbar('Failed to load report details', 'error')
      setViewDialog(false)
    } finally {
      setLoadingDetail(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.7) return '#10b981'
    if (confidence >= 0.4) return '#f59e0b'
    return '#ef4444'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.7) return 'High'
    if (confidence >= 0.4) return 'Medium'
    return 'Low'
  }

  const filteredReports = reports.filter(report => {
    const searchLower = searchTerm.toLowerCase()
    return (
      report.report_name?.toLowerCase().includes(searchLower) ||
      report.industry.toLowerCase().includes(searchLower) ||
      report.location.toLowerCase().includes(searchLower)
    )
  })

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
                  Saved Reports
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <ThemeToggle />
            </Box>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Page Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" gutterBottom>
            Saved Energy Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View, export, and manage your saved energy portfolio reports
          </Typography>
        </Box>

        {/* Search Bar */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search reports by name, industry, or location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Paper>

        {/* Reports Summary Stats */}
        {!loading && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Reports
                  </Typography>
                  <Typography variant="h4">{reports.length}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Average Confidence
                  </Typography>
                  <Typography variant="h4">
                    {reports.length > 0
                      ? (reports.reduce((sum, r) => sum + r.overall_confidence, 0) / reports.length * 100).toFixed(0)
                      : 0}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Latest Report
                  </Typography>
                  <Typography variant="h6">
                    {reports.length > 0
                      ? new Date(reports[0].created_at).toLocaleDateString()
                      : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Reports Table */}
        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 8 }}>
              <CircularProgress />
            </Box>
          ) : filteredReports.length === 0 ? (
            <Box sx={{ p: 8, textAlign: 'center' }}>
              <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm ? 'No reports found matching your search' : 'No saved reports yet'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {searchTerm
                  ? 'Try adjusting your search terms'
                  : 'Generate and save your first energy report to see it here'}
              </Typography>
              {!searchTerm && (
                <Button
                  variant="contained"
                  onClick={() => router.push('/dashboard/reports')}
                  startIcon={<AssessmentIcon />}
                >
                  Generate Report
                </Button>
              )}
            </Box>
          ) : (
            <TableContainer sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Report Name</strong></TableCell>
                    <TableCell><strong>Industry</strong></TableCell>
                    <TableCell><strong>Location</strong></TableCell>
                    <TableCell align="center"><strong>Confidence</strong></TableCell>
                    <TableCell align="center"><strong>Execution Time</strong></TableCell>
                    <TableCell align="center"><strong>Created</strong></TableCell>
                    <TableCell align="center"><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredReports.map((report) => (
                    <TableRow key={report.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {report.report_name || `Report #${report.id}`}
                        </Typography>
                      </TableCell>
                      <TableCell>{report.industry}</TableCell>
                      <TableCell>{report.location}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={`${(report.overall_confidence * 100).toFixed(0)}% ${getConfidenceLabel(report.overall_confidence)}`}
                          size="small"
                          sx={{
                            bgcolor: getConfidenceColor(report.overall_confidence),
                            color: 'white',
                            fontWeight: 500,
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        {report.execution_time.toFixed(1)}s
                      </TableCell>
                      <TableCell align="center">
                        {new Date(report.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} justifyContent="center">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleViewReport(report.id)}
                            title="View Details"
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => router.push(`/dashboard/chat?report_id=${report.id}&report_name=${encodeURIComponent(report.report_name || `Report ${report.id}`)}`)}
                            title="Talk to data"
                          >
                            <ChatIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="secondary"
                            onClick={() => handleExportPDF(report.id)}
                            disabled={exporting === report.id}
                            title="Export PDF"
                          >
                            {exporting === report.id ? (
                              <CircularProgress size={20} />
                            ) : (
                              <DownloadIcon fontSize="small" />
                            )}
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setDeleteDialog(report.id)}
                            disabled={deleting === report.id}
                            title="Delete Report"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      </Container>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog !== null}
        onClose={() => setDeleteDialog(null)}
      >
        <DialogTitle>Delete Report</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this report? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(null)}>Cancel</Button>
          <Button
            onClick={() => deleteDialog && handleDeleteReport(deleteDialog)}
            color="error"
            variant="contained"
            disabled={deleting !== null}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Report Dialog */}
      <Dialog
        open={viewDialog}
        onClose={() => setViewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Report Details</DialogTitle>
        <DialogContent>
          {loadingDetail ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedReport ? (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Report Name
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedReport.report_name || `Report #${selectedReport.id}`}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {new Date(selectedReport.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Industry
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedReport.profile_snapshot?.industry || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Location
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedReport.profile_snapshot?.location || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Overall Confidence
                  </Typography>
                  <Chip
                    label={`${(selectedReport.overall_confidence * 100).toFixed(0)}%`}
                    size="small"
                    sx={{
                      bgcolor: getConfidenceColor(selectedReport.overall_confidence),
                      color: 'white',
                      mt: 0.5,
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Execution Time
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedReport.execution_time.toFixed(1)}s
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Energy Mix Summary
                  </Typography>
                  {selectedReport.report_content?.optimization_agent?.optimized_mix?.length > 0 ? (
                    <Box sx={{ pl: 2 }}>
                      {selectedReport.report_content.optimization_agent.optimized_mix.map((item: any, idx: number) => (
                        <Typography key={idx} variant="body2">
                          • {item.source}: {item.percentage?.toFixed(1)}%
                        </Typography>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No energy mix data available
                    </Typography>
                  )}
                </Grid>
              </Grid>
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog(false)}>Close</Button>
          {selectedReport && (
            <Button
              onClick={() => {
                setViewDialog(false)
                handleExportPDF(selectedReport.id)
              }}
              variant="contained"
              startIcon={<DownloadIcon />}
            >
              Export PDF
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  )
}
