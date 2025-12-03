'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/components/ui/use-toast'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Home, Table as TableIcon, FileText, BarChart3, Code, Save, Download, Upload, Trash2, Shield, Loader2 } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'

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
  const { toast } = useToast()
  const router = useRouter()

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
    toast({
      title: 'Form Submitted',
      description: `Title: ${formData.title}`,
    })
    console.log('Form data:', formData)
  }

  const handleDeleteRow = (id: number) => {
    setTableData(tableData.filter((row) => row.id !== id))
    toast({
      title: 'Row Deleted',
      description: `Row ${id} has been removed`,
    })
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

    toast({
      title: 'Export Complete',
      description: 'Table data exported to CSV',
    })
  }

  const handleScrubPII = async () => {
    if (!piiText.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter text to scrub',
        variant: 'destructive',
      })
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

      toast({
        title: 'PII Scrubbed',
        description: `Found and masked ${response.data.detections} PII instance(s)`,
      })
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to scrub PII',
        variant: 'destructive',
      })
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="bg-white dark:bg-gray-950 border-b shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            <div className="flex items-center gap-2">
              <Code className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold">Utilities</h1>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="tables" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 max-w-2xl">
            <TabsTrigger value="tables">
              <TableIcon className="h-4 w-4 mr-2" />
              Tables
            </TabsTrigger>
            <TabsTrigger value="forms">
              <FileText className="h-4 w-4 mr-2" />
              Forms
            </TabsTrigger>
            <TabsTrigger value="charts">
              <BarChart3 className="h-4 w-4 mr-2" />
              Charts
            </TabsTrigger>
            <TabsTrigger value="pii">
              <Shield className="h-4 w-4 mr-2" />
              PII Scrubbing
            </TabsTrigger>
          </TabsList>

          {/* Tables Tab */}
          <TabsContent value="tables" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Data Table</CardTitle>
                    <CardDescription>Manage and view tabular data</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={exportTableToCSV}>
                      <Download className="h-4 w-4 mr-2" />
                      Export CSV
                    </Button>
                    <Button variant="outline" size="sm">
                      <Upload className="h-4 w-4 mr-2" />
                      Import
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tableData.map((row) => (
                        <TableRow key={row.id}>
                          <TableCell className="font-medium">{row.id}</TableCell>
                          <TableCell>{row.name}</TableCell>
                          <TableCell>{row.email}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{row.role}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={row.status === 'Active' ? 'default' : 'secondary'}>
                              {row.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteRow(row.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                  <span>Showing {tableData.length} rows</span>
                  <span>Total: {tableData.length} entries</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Forms Tab */}
          <TabsContent value="forms" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Sample Form</CardTitle>
                <CardDescription>Fill out the form with various input types</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleFormSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">Title *</Label>
                      <Input
                        id="title"
                        placeholder="Enter title"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="category">Category</Label>
                      <Input
                        id="category"
                        placeholder="Enter category"
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Input
                      id="description"
                      placeholder="Brief description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="priority">Priority</Label>
                    <Select
                      value={formData.priority}
                      onValueChange={(value) => setFormData({ ...formData, priority: value })}
                    >
                      <SelectTrigger id="priority">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="content">Content</Label>
                    <Textarea
                      id="content"
                      placeholder="Enter detailed content here..."
                      rows={5}
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    />
                  </div>

                  <div className="flex gap-3">
                    <Button type="submit">
                      <Save className="h-4 w-4 mr-2" />
                      Submit Form
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
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
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Line Chart</CardTitle>
                  <CardDescription>Documents and queries over time</CardDescription>
                </CardHeader>
                <CardContent>
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
                <CardHeader>
                  <CardTitle>Bar Chart</CardTitle>
                  <CardDescription>Document types distribution</CardDescription>
                </CardHeader>
                <CardContent>
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
                <CardHeader>
                  <CardTitle>Pie Chart</CardTitle>
                  <CardDescription>LLM provider usage</CardDescription>
                </CardHeader>
                <CardContent>
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
                <CardHeader>
                  <CardTitle>Statistics</CardTitle>
                  <CardDescription>Key metrics and numbers</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
                      <p className="text-3xl font-bold">120</p>
                    </div>
                    <FileText className="h-8 w-8 text-blue-500" />
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Queries</p>
                      <p className="text-3xl font-bold">584</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-green-500" />
                  </div>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Avg Confidence</p>
                      <p className="text-3xl font-bold">87%</p>
                    </div>
                    <Badge className="text-lg px-3 py-1">High</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* PII Scrubbing Tab */}
          <TabsContent value="pii" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  <CardTitle>PII Scrubbing</CardTitle>
                </div>
                <CardDescription>
                  Detect and mask Personally Identifiable Information (PII) like names, emails, phone numbers, and SSNs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="pii-input">Input Text</Label>
                  <Textarea
                    id="pii-input"
                    placeholder="Enter text containing PII... e.g., 'My name is John Doe and my email is john.doe@example.com. Call me at (555) 123-4567.'"
                    className="min-h-[150px] font-mono text-sm"
                    value={piiText}
                    onChange={(e) => setPiiText(e.target.value)}
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleScrubPII}
                    disabled={isScrubbing || !piiText.trim()}
                    className="flex-1"
                  >
                    {isScrubbing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Scrubbing...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Scrub PII
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleClearPII}
                    disabled={isScrubbing}
                  >
                    Clear
                  </Button>
                </div>

                {scrubbedText && (
                  <>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="pii-output">Scrubbed Text</Label>
                        <Badge variant={piiDetections > 0 ? 'default' : 'secondary'}>
                          {piiDetections} PII detected
                        </Badge>
                      </div>
                      <Textarea
                        id="pii-output"
                        className="min-h-[150px] font-mono text-sm bg-muted"
                        value={scrubbedText}
                        readOnly
                      />
                    </div>

                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        PII Detection Info
                      </h4>
                      <ul className="text-sm space-y-1 text-muted-foreground">
                        <li>• Names are replaced with <code className="px-1 py-0.5 bg-white rounded">{`{{NAME}}`}</code></li>
                        <li>• Emails are replaced with <code className="px-1 py-0.5 bg-white rounded">{`{{EMAIL}}`}</code></li>
                        <li>• Phone numbers are replaced with <code className="px-1 py-0.5 bg-white rounded">{`{{PHONE}}`}</code></li>
                        <li>• SSNs and other IDs are replaced with <code className="px-1 py-0.5 bg-white rounded">{`{{SSN}}`}</code></li>
                      </ul>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Example Use Cases</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">Data Anonymization</h4>
                    <p className="text-sm text-muted-foreground">
                      Anonymize customer data before sharing with third-party analytics or training ML models.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">Compliance</h4>
                    <p className="text-sm text-muted-foreground">
                      Meet GDPR, CCPA, and HIPAA requirements by removing PII from logs and documents.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">Testing Data</h4>
                    <p className="text-sm text-muted-foreground">
                      Create safe test datasets by masking production data containing sensitive information.
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">Public Sharing</h4>
                    <p className="text-sm text-muted-foreground">
                      Safely share documents publicly by removing names, contact info, and identifiers.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
