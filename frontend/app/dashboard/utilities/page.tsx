'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  TextField,
  MenuItem,
  Tabs,
  Tab,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
} from '@mui/material'
import {
  Home as HomeIcon,
  TableChart as TableIcon,
  Description as FileTextIcon,
  BarChart as BarChartIcon,
  Code as CodeIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'

interface TableRow {
  id: number
  name: string
  email: string
  role: string
  status: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

export default function UtilitiesPage() {
  const { user } = useAuth()
  const { showSnackbar } = useSnackbar()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState(0)

  // Sample data for tables
  const [tableData, setTableData] = useState<TableRow[]>([
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin', status: 'Active' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User', status: 'Active' },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'Analyst', status: 'Inactive' },
    { id: 4, name: 'Alice Brown', email: 'alice@example.com', role: 'User', status: 'Active' },
    { id: 5, name: 'Charlie Wilson', email: 'charlie@example.com', role: 'Viewer', status: 'Active' },
  ])

  // Sample data for charts
  const lineChartData = [
    { month: 'Jan', documents: 12, queries: 45 },
    { month: 'Feb', documents: 19, queries: 67 },
    { month: 'Mar', documents: 25, queries: 89 },
    { month: 'Apr', documents: 31, queries: 102 },
    { month: 'May', documents: 38, queries: 125 },
    { month: 'Jun', documents: 45, queries: 156 },
  ]

  const barChartData = [
    { category: 'PDFs', count: 45 },
    { category: 'Text Files', count: 32 },
    { category: 'CSVs', count: 28 },
    { category: 'DOCX', count: 15 },
  ]

  const pieChartData = [
    { name: 'Custom API', value: 65 },
    { name: 'Ollama', value: 35 },
  ]

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    priority: 'medium',
    content: '',
  })

  // PII Scrubbing state
  const [piiText, setPiiText] = useState('')
  const [scrubbedText, setScrubbedText] = useState('')
  const [piiDetections, setPiiDetections] = useState(0)
  const [isScrubbing, setIsScrubbing] = useState(false)

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    showSnackbar(`Form Submitted: ${formData.title}`, 'success')
    console.log('Form data:', formData)
  }

  const handleDeleteRow = (id: number) => {
    setTableData(tableData.filter((row) => row.id !== id))
    showSnackbar(`Row ${id} has been removed`, 'success')
  }

  const exportTableToCSV = () => {
    const csv = [
      ['ID', 'Name', 'Email', 'Role', 'Status'],
      ...tableData.map((row) => [row.id, row.name, row.email, row.role, row.status]),
    ]
      .map((row) => row.join(','))
      .join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'table-data.csv'
    a.click()

    showSnackbar('Table data exported to CSV', 'success')
  }

  const handleScrubPII = async () => {
    if (!piiText.trim()) {
      showSnackbar('Please enter text to scrub', 'error')
      return
    }

    setIsScrubbing(true)
    try {
      const response = await api.post('/utilities/scrub-pii', {
        text: piiText,
        locale: 'en_US',
      })

      setScrubbedText(response.data.scrubbed_text)
      setPiiDetections(response.data.detections)

      showSnackbar(`Found and masked ${response.data.detections} PII instance(s)`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to scrub PII', 'error')
    } finally {
      setIsScrubbing(false)
    }
  }

  const handleClearPII = () => {
    setPiiText('')
    setScrubbedText('')
    setPiiDetections(0)
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
                <CodeIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  Utilities
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
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<TableIcon />} iconPosition="start" label="Tables" />
            <Tab icon={<FileTextIcon />} iconPosition="start" label="Forms" />
            <Tab icon={<BarChartIcon />} iconPosition="start" label="Charts" />
            <Tab icon={<ShieldIcon />} iconPosition="start" label="PII Scrubbing" />
          </Tabs>
        </Paper>

        {/* Tables Tab */}
        {activeTab === 0 && (
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, mt: 2 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Data Table
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Manage and view tabular data
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<DownloadIcon />}
                    onClick={exportTableToCSV}
                  >
                    Export CSV
                  </Button>
                  <Button variant="outlined" size="small" startIcon={<UploadIcon />}>
                    Import
                  </Button>
                </Box>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tableData.map((row) => (
                      <TableRow key={row.id} hover>
                        <TableCell sx={{ fontWeight: 600 }}>{row.id}</TableCell>
                        <TableCell>{row.name}</TableCell>
                        <TableCell>{row.email}</TableCell>
                        <TableCell>
                          <Chip label={row.role} variant="outlined" size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={row.status}
                            color={row.status === 'Active' ? 'primary' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteRow(row.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Showing {tableData.length} rows
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total: {tableData.length} entries
                </Typography>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Forms Tab */}
        {activeTab === 1 && (
          <Card>
            <CardContent>
              <Box sx={{ mb: 3, mt: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Sample Form
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Fill out the form with various input types
                </Typography>
              </Box>

              <Box component="form" onSubmit={handleFormSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                  <TextField
                    label="Title *"
                    placeholder="Enter title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    fullWidth
                  />

                  <TextField
                    label="Category"
                    placeholder="Enter category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    fullWidth
                  />
                </Box>

                <TextField
                  label="Description"
                  placeholder="Brief description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  fullWidth
                />

                <FormControl fullWidth>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={formData.priority}
                    label="Priority"
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="urgent">Urgent</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Content"
                  placeholder="Enter detailed content here..."
                  multiline
                  rows={5}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  fullWidth
                />

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button type="submit" variant="contained" startIcon={<SaveIcon />}>
                    Submit Form
                  </Button>
                  <Button
                    type="button"
                    variant="outlined"
                    onClick={() =>
                      setFormData({
                        title: '',
                        description: '',
                        category: '',
                        priority: 'medium',
                        content: '',
                      })
                    }
                  >
                    Reset
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Charts Tab */}
        {activeTab === 2 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, mt: 2 }}>
                  Line Chart
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Documents and queries over time
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={lineChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="documents" stroke="#8884d8" strokeWidth={2} />
                    <Line type="monotone" dataKey="queries" stroke="#82ca9d" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, mt: 2 }}>
                  Bar Chart
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Document types distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, mt: 2 }}>
                  Pie Chart
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  LLM provider usage
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, mt: 2 }}>
                  Statistics
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Key metrics and numbers
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Total Documents
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        120
                      </Typography>
                    </Box>
                    <FileTextIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
                  </Paper>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Total Queries
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        584
                      </Typography>
                    </Box>
                    <BarChartIcon sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
                  </Paper>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Avg Confidence
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        87%
                      </Typography>
                    </Box>
                    <Chip label="High" color="primary" sx={{ fontSize: 16, px: 1 }} />
                  </Paper>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* PII Scrubbing Tab */}
        {activeTab === 3 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, mb: 1 }}>
                  <ShieldIcon color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    PII Scrubbing
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Detect and mask Personally Identifiable Information (PII) like names, emails, phone numbers, and SSNs
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <TextField
                    label="Input Text"
                    placeholder="Enter text containing PII... e.g., 'My name is John Doe and my email is john.doe@example.com. Call me at (555) 123-4567.'"
                    multiline
                    rows={6}
                    value={piiText}
                    onChange={(e) => setPiiText(e.target.value)}
                    fullWidth
                    sx={{ '& textarea': { fontFamily: 'monospace', fontSize: '0.875rem' } }}
                  />

                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      startIcon={isScrubbing ? <CircularProgress size={16} /> : <ShieldIcon />}
                      onClick={handleScrubPII}
                      disabled={isScrubbing || !piiText.trim()}
                      fullWidth
                    >
                      {isScrubbing ? 'Scrubbing...' : 'Scrub PII'}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={handleClearPII}
                      disabled={isScrubbing}
                    >
                      Clear
                    </Button>
                  </Box>

                  {scrubbedText && (
                    <>
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2">Scrubbed Text</Typography>
                          <Chip
                            label={`${piiDetections} PII detected`}
                            color={piiDetections > 0 ? 'primary' : 'default'}
                            size="small"
                          />
                        </Box>
                        <TextField
                          multiline
                          rows={6}
                          value={scrubbedText}
                          fullWidth
                          InputProps={{ readOnly: true }}
                          sx={{
                            '& textarea': { fontFamily: 'monospace', fontSize: '0.875rem' },
                            '& .MuiInputBase-root': { bgcolor: 'action.hover' },
                          }}
                        />
                      </Box>

                      <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <ShieldIcon fontSize="small" />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            PII Detection Info
                          </Typography>
                        </Box>
                        <Box component="ul" sx={{ pl: 2, m: 0 }}>
                          <Typography component="li" variant="body2">
                            Names are replaced with <code style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.9)', borderRadius: 4 }}>{`{{NAME}}`}</code>
                          </Typography>
                          <Typography component="li" variant="body2">
                            Emails are replaced with <code style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.9)', borderRadius: 4 }}>{`{{EMAIL}}`}</code>
                          </Typography>
                          <Typography component="li" variant="body2">
                            Phone numbers are replaced with <code style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.9)', borderRadius: 4 }}>{`{{PHONE}}`}</code>
                          </Typography>
                          <Typography component="li" variant="body2">
                            SSNs and other IDs are replaced with <code style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.9)', borderRadius: 4 }}>{`{{SSN}}`}</code>
                          </Typography>
                        </Box>
                      </Paper>
                    </>
                  )}
                </Box>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, mt: 2 }}>
                  Example Use Cases
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Data Anonymization
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Anonymize customer data before sharing with third-party analytics or training ML models.
                    </Typography>
                  </Paper>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Compliance
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Meet GDPR, CCPA, and HIPAA requirements by removing PII from logs and documents.
                    </Typography>
                  </Paper>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Testing Data
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Create safe test datasets by masking production data containing sensitive information.
                    </Typography>
                  </Paper>
                  <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Public Sharing
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Safely share documents publicly by removing names, contact info, and identifiers.
                    </Typography>
                  </Paper>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}
      </Container>
    </Box>
  )
}
