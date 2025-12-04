'use client'

import React, { useState, useMemo } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  TextField,
  Typography,
  Box,
  Chip,
  InputAdornment,
  Alert,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import DescriptionIcon from '@mui/icons-material/Description'
import PublicIcon from '@mui/icons-material/Public'
import PersonIcon from '@mui/icons-material/Person'

interface Document {
  id: string
  title: string | null
  filename: string
  file_type: string
  scope: 'global' | 'user'
  auto_summary?: string | null
}

interface DocumentSelectionModalProps {
  open: boolean
  onClose: () => void
  onConfirm: (selectedIds: string[]) => void
  documents: Document[]
}

export default function DocumentSelectionModal({
  open,
  onClose,
  onConfirm,
  documents,
}: DocumentSelectionModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectAll, setSelectAll] = useState(false)

  // Filter documents based on search query
  const filteredDocuments = useMemo(() => {
    if (!searchQuery) return documents

    const query = searchQuery.toLowerCase()
    return documents.filter(
      (doc) =>
        doc.title?.toLowerCase().includes(query) ||
        doc.filename.toLowerCase().includes(query) ||
        doc.file_type.toLowerCase().includes(query) ||
        doc.auto_summary?.toLowerCase().includes(query)
    )
  }, [documents, searchQuery])

  const handleToggle = (docId: string) => {
    setSelectedIds((prev) =>
      prev.includes(docId)
        ? prev.filter((id) => id !== docId)
        : [...prev, docId]
    )
  }

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredDocuments.map((doc) => doc.id))
    }
    setSelectAll(!selectAll)
  }

  const handleConfirm = () => {
    onConfirm(selectedIds)
    handleClose()
  }

  const handleClose = () => {
    setSelectedIds([])
    setSearchQuery('')
    setSelectAll(false)
    onClose()
  }

  const getFileIcon = (fileType: string) => {
    return <DescriptionIcon color="action" />
  }

  const getScopeChip = (scope: 'global' | 'user') => {
    if (scope === 'global') {
      return (
        <Chip
          icon={<PublicIcon />}
          label="Global"
          size="small"
          color="error"
          variant="outlined"
        />
      )
    }
    return (
      <Chip
        icon={<PersonIcon />}
        label="Personal"
        size="small"
        color="primary"
        variant="outlined"
      />
    )
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Select Documents for Conversation
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Choose which documents to search in this conversation. Leave empty to search all available documents.
        </Typography>
      </DialogTitle>

      <DialogContent dividers>
        {/* Search Bar */}
        <TextField
          fullWidth
          placeholder="Search documents by title, filename, or content..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ mb: 2 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />

        {/* Select All Checkbox */}
        <Box sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
          <Checkbox
            checked={selectAll}
            indeterminate={
              selectedIds.length > 0 &&
              selectedIds.length < filteredDocuments.length
            }
            onChange={handleSelectAll}
          />
          <Typography variant="body2" color="text.secondary">
            Select All ({filteredDocuments.length} documents)
          </Typography>
        </Box>

        {/* Document List */}
        {filteredDocuments.length === 0 ? (
          <Alert severity="info">
            {searchQuery
              ? 'No documents match your search.'
              : 'No documents available. Upload documents to get started.'}
          </Alert>
        ) : (
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {filteredDocuments.map((doc) => (
              <ListItem key={doc.id} disablePadding>
                <ListItemButton
                  dense
                  onClick={() => handleToggle(doc.id)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon>
                    <Checkbox
                      edge="start"
                      checked={selectedIds.includes(doc.id)}
                      tabIndex={-1}
                      disableRipple
                    />
                  </ListItemIcon>
                  <ListItemIcon>{getFileIcon(doc.file_type)}</ListItemIcon>
                  <ListItemText
                    primary={
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          flexWrap: 'wrap',
                        }}
                      >
                        <Typography variant="body1">
                          {doc.title || doc.filename}
                        </Typography>
                        {getScopeChip(doc.scope)}
                        <Chip
                          label={doc.file_type.toUpperCase()}
                          size="small"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      </Box>
                    }
                    secondary={
                      <>
                        {doc.title && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            display="block"
                          >
                            {doc.filename}
                          </Typography>
                        )}
                        {doc.auto_summary && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            display="block"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              mt: 0.5,
                            }}
                          >
                            {doc.auto_summary}
                          </Typography>
                        )}
                      </>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Box sx={{ flex: 1 }}>
          {selectedIds.length > 0 && (
            <Typography variant="body2" color="text.secondary">
              {selectedIds.length} document{selectedIds.length !== 1 ? 's' : ''} selected
            </Typography>
          )}
        </Box>
        <Button onClick={handleClose} color="inherit">
          Cancel
        </Button>
        <Button onClick={handleConfirm} variant="contained" disabled={documents.length === 0}>
          {selectedIds.length === 0 ? 'Use All Documents' : `Start Conversation (${selectedIds.length})`}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
