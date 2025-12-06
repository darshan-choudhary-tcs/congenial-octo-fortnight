'use client'

import React, { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Stack,
  Chip,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material'
import { reportsAPI } from '@/lib/api'

interface TextualReportEditorProps {
  reportId: number
  reportName?: string
  existingTextualVersion?: {
    generated_text?: string
    edited_text?: string
    generated_at?: string
    edited_at?: string
    edit_count?: number
  }
  onUpdate?: () => void
}

export default function TextualReportEditor({
  reportId,
  reportName,
  existingTextualVersion,
  onUpdate,
}: TextualReportEditorProps) {
  const [expanded, setExpanded] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false)
  const [textualVersion, setTextualVersion] = useState<any>(existingTextualVersion || null)
  const [editedText, setEditedText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Determine which text to display
  const displayText = textualVersion?.edited_text || textualVersion?.generated_text || ''

  const handleGenerateTextualVersion = async () => {
    setIsGenerating(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const response = await reportsAPI.generateTextualVersion(reportId)
      setTextualVersion(response.data.textual_version)
      setEditedText(response.data.textual_version.generated_text)
      setSuccessMessage('Textual version generated successfully!')
      setExpanded(true)
      if (onUpdate) onUpdate()
    } catch (err: any) {
      console.error('Error generating textual version:', err)
      setError(err.response?.data?.detail || 'Failed to generate textual version')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleStartEditing = () => {
    setIsEditing(true)
    setEditedText(displayText)
    setError(null)
    setSuccessMessage(null)
  }

  const handleCancelEditing = () => {
    setIsEditing(false)
    setEditedText('')
  }

  const handleSaveEdits = async () => {
    if (!editedText.trim()) {
      setError('Text cannot be empty')
      return
    }

    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const response = await reportsAPI.updateTextualVersion(reportId, editedText)
      setTextualVersion(response.data.textual_version)
      setIsEditing(false)
      setSuccessMessage('Changes saved successfully!')
      if (onUpdate) onUpdate()
    } catch (err: any) {
      console.error('Error saving textual version:', err)
      setError(err.response?.data?.detail || 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDownload = async () => {
    setIsDownloading(true)
    setError(null)

    try {
      const response = await reportsAPI.downloadTextualVersion(reportId)

      if (!response.ok) {
        throw new Error('Failed to download textual version')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportName || 'Energy_Report'}_Textual_Version.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccessMessage('Text report downloaded successfully!')
    } catch (err: any) {
      console.error('Error downloading textual version:', err)
      setError('Failed to download textual version')
    } finally {
      setIsDownloading(false)
    }
  }

  const handleDownloadPDF = async () => {
    setIsDownloadingPDF(true)
    setError(null)

    try {
      const { jsPDF } = await import('jspdf')
      const doc = new jsPDF()

      const text = displayText
      const pageWidth = doc.internal.pageSize.getWidth()
      const pageHeight = doc.internal.pageSize.getHeight()
      const margin = 15
      const maxWidth = pageWidth - 2 * margin
      const lineHeight = 7
      let yPosition = margin

      // Add title
      doc.setFontSize(16)
      doc.setFont('helvetica', 'bold')
      doc.text(reportName || 'Energy Report - Textual Version', margin, yPosition)
      yPosition += lineHeight * 2

      // Split text into lines that fit the page width
      doc.setFontSize(11)
      doc.setFont('helvetica', 'normal')
      const lines = doc.splitTextToSize(text, maxWidth)

      // Add each line, creating new pages as needed
      for (let i = 0; i < lines.length; i++) {
        if (yPosition + lineHeight > pageHeight - margin) {
          doc.addPage()
          yPosition = margin
        }
        doc.text(lines[i], margin, yPosition)
        yPosition += lineHeight
      }

      // Save the PDF
      doc.save(`${reportName || 'Energy_Report'}_Textual_Version.pdf`)
      setSuccessMessage('PDF report downloaded successfully!')
    } catch (err: any) {
      console.error('Error generating PDF:', err)
      setError('Failed to generate PDF')
    } finally {
      setIsDownloadingPDF(false)
    }
  }

  return (
    <Card sx={{ mt: 3, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h6" fontWeight="600">
              Textual Report Version
            </Typography>
            {textualVersion && (
              <Chip
                label={textualVersion.edited_text ? 'Reviewed' : 'Generated'}
                color={textualVersion.edited_text ? 'success' : 'info'}
                size="small"
              />
            )}
          </Box>
          <IconButton
            onClick={() => setExpanded(!expanded)}
            sx={{
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s',
            }}
          >
            <ExpandMoreIcon />
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={2}>
          Generate a comprehensive narrative version of this report for human review and editing.
          This version excludes charts and UI elements, providing a full textual analysis.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {successMessage && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
            {successMessage}
          </Alert>
        )}

        {!textualVersion && !expanded && (
          <Button
            variant="contained"
            startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <VisibilityIcon />}
            onClick={handleGenerateTextualVersion}
            disabled={isGenerating}
            fullWidth
          >
            {isGenerating ? 'Generating...' : 'Review - Generate Textual Version'}
          </Button>
        )}

        <Collapse in={expanded}>
          {!textualVersion ? (
            <Box textAlign="center" py={4}>
              <Button
                variant="contained"
                size="large"
                startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
                onClick={handleGenerateTextualVersion}
                disabled={isGenerating}
              >
                {isGenerating ? 'Generating Textual Version...' : 'Generate Textual Version'}
              </Button>
            </Box>
          ) : (
            <Box>
              {textualVersion.generated_at && (
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary">
                    Generated: {new Date(textualVersion.generated_at).toLocaleString()}
                  </Typography>
                  {textualVersion.edited_at && (
                    <>
                      {' • '}
                      <Typography variant="caption" color="text.secondary">
                        Last Edited: {new Date(textualVersion.edited_at).toLocaleString()}
                      </Typography>
                      {' • '}
                      <Typography variant="caption" color="text.secondary">
                        Edit Count: {textualVersion.edit_count || 0}
                      </Typography>
                    </>
                  )}
                </Box>
              )}

              {isEditing ? (
                <Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={20}
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    variant="outlined"
                    sx={{
                      mb: 2,
                      '& .MuiInputBase-root': {
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                      },
                    }}
                  />
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      startIcon={isSaving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                      onClick={handleSaveEdits}
                      disabled={isSaving}
                    >
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                    <Button variant="outlined" onClick={handleCancelEditing} disabled={isSaving}>
                      Cancel
                    </Button>
                  </Stack>
                </Box>
              ) : (
                <Box>
                  <Box
                    sx={{
                      p: 3,
                      bgcolor: 'background.default',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      maxHeight: '500px',
                      overflowY: 'auto',
                      mb: 2,
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'Georgia, serif',
                      fontSize: '0.95rem',
                      lineHeight: 1.8,
                    }}
                  >
                    {displayText}
                  </Box>
                  <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
                    <Button
                      variant="contained"
                      startIcon={<EditIcon />}
                      onClick={handleStartEditing}
                    >
                      Edit Text
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={isDownloading ? <CircularProgress size={20} /> : <DownloadIcon />}
                      onClick={handleDownload}
                      disabled={isDownloading || isDownloadingPDF}
                    >
                      {isDownloading ? 'Downloading...' : 'Download as TXT'}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={isDownloadingPDF ? <CircularProgress size={20} /> : <DownloadIcon />}
                      onClick={handleDownloadPDF}
                      disabled={isDownloading || isDownloadingPDF}
                    >
                      {isDownloadingPDF ? 'Generating...' : 'Download as PDF'}
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={isGenerating ? <CircularProgress size={20} /> : <RefreshIcon />}
                      onClick={handleGenerateTextualVersion}
                      disabled={isGenerating}
                    >
                      Regenerate
                    </Button>
                  </Stack>
                </Box>
              )}
            </Box>
          )}
        </Collapse>
      </CardContent>
    </Card>
  )
}
