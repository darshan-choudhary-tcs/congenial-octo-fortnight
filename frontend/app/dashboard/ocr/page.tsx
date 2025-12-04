'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  TextField,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  Paper,
  LinearProgress,
  Switch,
  FormControlLabel,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ArrowBack as ArrowLeftIcon,
  Upload as UploadIcon,
  Description as FileTextIcon,
  Image as ImageIcon,
  InsertDriveFile as FileTypeIcon,
  Download as DownloadIcon,
  Save as SaveIcon,
  CheckCircle as CheckCircleIcon,
  Home as HomeIcon,
  CameraAlt as CameraIcon,
} from '@mui/icons-material';
import { useSnackbar } from '@/components/SnackbarProvider';
import { ThemeToggle } from '@/components/ThemeToggle';

interface OCRPageResult {
  page_number: number;
  extracted_text: string;
  confidence: number;
  image_size: number[];
  tokens_used: number;
}

interface OCRResult {
  file_name: string;
  file_type: string;
  file_size: number;
  provider: string;
  model: string;
  extracted_text: string;
  total_tokens_used: number;
  total_pages?: number;
  processed_pages?: number;
  pages?: OCRPageResult[];
  image_size?: number[];
  image_mode?: string;
  confidence?: number;
  document_id?: string;
}

export default function OCRPage() {
  const router = useRouter();
  const { showSnackbar } = useSnackbar();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>('custom');
  const [processAllPages, setProcessAllPages] = useState<boolean>(true);
  const [maxPages, setMaxPages] = useState<string>('');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [saveToVectorStore, setSaveToVectorStore] = useState<boolean>(false);
  const [title, setTitle] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [selectedPage, setSelectedPage] = useState<number>(1);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setTitle(`OCR: ${file.name}`);

      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setPreviewUrl(event.target?.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        setPreviewUrl(null);
      }

      // Reset results
      setOcrResult(null);
    }
  };

  const handleProcessOCR = async () => {
    if (!selectedFile) {
      showSnackbar('Please select an image or PDF file to process', 'error');
      return;
    }

    setIsProcessing(true);
    setOcrResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('provider', provider);
      formData.append('process_all_pages', processAllPages.toString());
      if (maxPages) {
        formData.append('max_pages', maxPages);
      }
      if (customPrompt) {
        formData.append('custom_prompt', customPrompt);
      }
      formData.append('save_to_vector_store', saveToVectorStore.toString());
      if (saveToVectorStore && title) {
        formData.append('title', title);
      }

      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/documents/ocr', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'OCR processing failed');
      }

      const result: OCRResult = await response.json();
      setOcrResult(result);
      setSelectedPage(1);

      showSnackbar(`Extracted text from ${result.file_name}`, 'success');
    } catch (error: any) {
      showSnackbar(error.message, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadText = () => {
    if (!ocrResult) return;

    const blob = new Blob([ocrResult.extracted_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ocrResult.file_name}_ocr.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showSnackbar('OCR text has been downloaded', 'success');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

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
                <CameraIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  OCR Processing
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
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
        {/* Left Column - Upload & Settings */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* File Upload Card */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, mt: 2 }}>
                <UploadIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Upload File
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Select an image or PDF file for OCR processing
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Button variant="contained" component="label" startIcon={<UploadIcon />} disabled={isProcessing}>
                    Choose File
                    <input
                      type="file"
                      hidden
                      accept=".jpg,.jpeg,.png,.pdf,.tiff,.tif,.bmp,.webp"
                      onChange={handleFileChange}
                    />
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Supported: JPG, PNG, PDF, TIFF, BMP, WebP (Max 20MB)
                  </Typography>
                </Box>

                {selectedFile && (
                  <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {selectedFile.type.startsWith('image/') ? (
                        <ImageIcon fontSize="small" />
                      ) : (
                        <FileTypeIcon fontSize="small" />
                      )}
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {selectedFile.name}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Size: {formatFileSize(selectedFile.size)}
                    </Typography>
                  </Paper>
                )}

                {previewUrl && (
                  <Paper sx={{ p: 1, border: 1, borderColor: 'divider' }}>
                    <img src={previewUrl} alt="Preview" style={{ width: '100%', maxHeight: 256, objectFit: 'contain' }} />
                  </Paper>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Settings Card */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, mt: 2 }}>
                OCR Settings
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Vision Model Provider</InputLabel>
                  <Select
                    value={provider}
                    label="Vision Model Provider"
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={isProcessing}
                  >
                    <MenuItem value="custom">Custom (Azure Llama-3.2-90B-Vision)</MenuItem>
                    <MenuItem value="ollama">Ollama (llama3.2-vision)</MenuItem>
                  </Select>
                </FormControl>

                {selectedFile?.type === 'application/pdf' && (
                  <>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={processAllPages}
                          onChange={(e) => setProcessAllPages(e.target.checked)}
                          disabled={isProcessing}
                        />
                      }
                      label="Process all pages"
                    />

                    {!processAllPages && (
                      <TextField
                        label="Maximum pages to process"
                        type="number"
                        value={maxPages}
                        onChange={(e) => setMaxPages(e.target.value)}
                        placeholder="e.g., 5"
                        disabled={isProcessing}
                        inputProps={{ min: 1 }}
                        fullWidth
                      />
                    )}
                  </>
                )}

                <TextField
                  label="Custom OCR Prompt (Optional)"
                  multiline
                  rows={3}
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Enter custom instructions for text extraction..."
                  disabled={isProcessing}
                  fullWidth
                />

                <Divider />

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={saveToVectorStore}
                        onChange={(e) => setSaveToVectorStore(e.target.checked)}
                        disabled={isProcessing}
                      />
                    }
                    label="Save to Knowledge Base"
                  />

                  {saveToVectorStore && (
                    <TextField
                      label="Document Title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Enter document title..."
                      disabled={isProcessing}
                      fullWidth
                    />
                  )}
                </Box>

                <Button
                  variant="contained"
                  onClick={handleProcessOCR}
                  disabled={!selectedFile || isProcessing}
                  startIcon={isProcessing ? null : <FileTextIcon />}
                  fullWidth
                >
                  {isProcessing ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress sx={{ width: 20, height: 20 }} />
                      Processing OCR...
                    </Box>
                  ) : (
                    'Process OCR'
                  )}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Right Column - Results */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {ocrResult ? (
            <>
              {/* Results Info Card */}
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, mt: 2 }}>
                    <CheckCircleIcon color="success" />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      OCR Results
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        File:
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {ocrResult.file_name}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Type:
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                        {ocrResult.file_type}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Provider:
                      </Typography>
                      <Chip label={ocrResult.provider} variant="outlined" size="small" />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Model:
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {ocrResult.model}
                      </Typography>
                    </Box>
                    {ocrResult.total_pages && (
                      <>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Total Pages:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {ocrResult.total_pages}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Processed:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {ocrResult.processed_pages}
                          </Typography>
                        </Box>
                      </>
                    )}
                    {ocrResult.confidence && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Confidence:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {(ocrResult.confidence * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    )}
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Tokens Used:
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {ocrResult.total_tokens_used}
                      </Typography>
                    </Box>
                  </Box>

                  {ocrResult.document_id && (
                    <Paper sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText', mb: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        ✓ Saved to Knowledge Base
                      </Typography>
                      <Typography variant="caption">
                        Document ID: {ocrResult.document_id}
                      </Typography>
                    </Paper>
                  )}

                  <Button
                    variant="outlined"
                    onClick={handleDownloadText}
                    startIcon={<DownloadIcon />}
                    fullWidth
                  >
                    Download Text
                  </Button>
                </CardContent>
              </Card>

              {/* Extracted Text Card */}
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, mt: 2 }}>
                    Extracted Text
                  </Typography>

                  {ocrResult.pages && ocrResult.pages.length > 1 ? (
                    <>
                      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
                        {ocrResult.pages.map((page, index) => (
                          <Tab key={page.page_number} label={`Page ${page.page_number}`} />
                        ))}
                      </Tabs>
                      {ocrResult.pages.map((page, index) => (
                        activeTab === index && (
                          <Box key={page.page_number}>
                            <Paper
                              sx={{
                                p: 2,
                                maxHeight: 500,
                                overflow: 'auto',
                                border: 1,
                                borderColor: 'divider',
                                mb: 1,
                              }}
                            >
                              <Typography
                                component="pre"
                                variant="body2"
                                sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', m: 0 }}
                              >
                                {page.extracted_text}
                              </Typography>
                            </Paper>
                            <Typography variant="caption" color="text.secondary">
                              Confidence: {(page.confidence * 100).toFixed(1)}% | Tokens: {page.tokens_used}
                            </Typography>
                          </Box>
                        )
                      ))}
                    </>
                  ) : (
                    <Paper
                      sx={{
                        p: 2,
                        maxHeight: 500,
                        overflow: 'auto',
                        border: 1,
                        borderColor: 'divider',
                      }}
                    >
                      <Typography
                        component="pre"
                        variant="body2"
                        sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', m: 0 }}
                      >
                        {ocrResult.extracted_text}
                      </Typography>
                    </Paper>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 16, textAlign: 'center' }}>
                <FileTextIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  No results yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upload a file and click &quot;Process OCR&quot; to extract text
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>
      </Container>
    </Box>
  );
}
