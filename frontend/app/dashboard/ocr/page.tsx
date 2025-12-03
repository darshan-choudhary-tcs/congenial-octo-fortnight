'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { ArrowLeft, Upload, FileText, Image as ImageIcon, FileType, Loader2, Download, Save, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';

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
  const { toast } = useToast();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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
      toast({
        title: 'No file selected',
        description: 'Please select an image or PDF file to process',
        variant: 'destructive',
      });
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

      toast({
        title: 'OCR completed successfully',
        description: `Extracted text from ${result.file_name}`,
      });
    } catch (error: any) {
      toast({
        title: 'OCR processing failed',
        description: error.message,
        variant: 'destructive',
      });
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

    toast({
      title: 'Downloaded',
      description: 'OCR text has been downloaded',
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={() => router.push('/dashboard')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">OCR Processing</h1>
            <p className="text-muted-foreground">Extract text from images and PDFs using AI vision models</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Upload & Settings */}
        <div className="space-y-6">
          {/* File Upload Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload File
              </CardTitle>
              <CardDescription>Select an image or PDF file for OCR processing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="file">File</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf,.tiff,.tif,.bmp,.webp"
                  onChange={handleFileChange}
                  disabled={isProcessing}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Supported: JPG, PNG, PDF, TIFF, BMP, WebP (Max 20MB)
                </p>
              </div>

              {selectedFile && (
                <div className="p-3 bg-muted rounded-lg space-y-2">
                  <div className="flex items-center gap-2">
                    {selectedFile.type.startsWith('image/') ? (
                      <ImageIcon className="h-4 w-4" />
                    ) : (
                      <FileType className="h-4 w-4" />
                    )}
                    <span className="font-medium">{selectedFile.name}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Size: {formatFileSize(selectedFile.size)}
                  </div>
                </div>
              )}

              {previewUrl && (
                <div className="border rounded-lg p-2">
                  <img src={previewUrl} alt="Preview" className="w-full h-auto max-h-64 object-contain" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Settings Card */}
          <Card>
            <CardHeader>
              <CardTitle>OCR Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="provider">Vision Model Provider</Label>
                <Select value={provider} onValueChange={setProvider} disabled={isProcessing}>
                  <SelectTrigger id="provider">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="custom">Custom (Azure Llama-3.2-90B-Vision)</SelectItem>
                    <SelectItem value="ollama">Ollama (llama3.2-vision)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {selectedFile?.type === 'application/pdf' && (
                <>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="processAllPages"
                      checked={processAllPages}
                      onChange={(e) => setProcessAllPages(e.target.checked)}
                      disabled={isProcessing}
                      className="rounded"
                    />
                    <Label htmlFor="processAllPages">Process all pages</Label>
                  </div>

                  {!processAllPages && (
                    <div>
                      <Label htmlFor="maxPages">Maximum pages to process</Label>
                      <Input
                        id="maxPages"
                        type="number"
                        value={maxPages}
                        onChange={(e) => setMaxPages(e.target.value)}
                        placeholder="e.g., 5"
                        disabled={isProcessing}
                        min="1"
                      />
                    </div>
                  )}
                </>
              )}

              <div>
                <Label htmlFor="customPrompt">Custom OCR Prompt (Optional)</Label>
                <Textarea
                  id="customPrompt"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Enter custom instructions for text extraction..."
                  disabled={isProcessing}
                  rows={3}
                />
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="saveToVectorStore"
                    checked={saveToVectorStore}
                    onChange={(e) => setSaveToVectorStore(e.target.checked)}
                    disabled={isProcessing}
                    className="rounded"
                  />
                  <Label htmlFor="saveToVectorStore">Save to Knowledge Base</Label>
                </div>

                {saveToVectorStore && (
                  <div>
                    <Label htmlFor="title">Document Title</Label>
                    <Input
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Enter document title..."
                      disabled={isProcessing}
                    />
                  </div>
                )}
              </div>

              <Button onClick={handleProcessOCR} disabled={!selectedFile || isProcessing} className="w-full">
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing OCR...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Process OCR
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Results */}
        <div className="space-y-6">
          {ocrResult ? (
            <>
              {/* Results Info Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    OCR Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-muted-foreground">File:</span>
                      <p className="font-medium">{ocrResult.file_name}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Type:</span>
                      <p className="font-medium capitalize">{ocrResult.file_type}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Provider:</span>
                      <Badge variant="outline">{ocrResult.provider}</Badge>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Model:</span>
                      <p className="font-medium text-xs">{ocrResult.model}</p>
                    </div>
                    {ocrResult.total_pages && (
                      <>
                        <div>
                          <span className="text-muted-foreground">Total Pages:</span>
                          <p className="font-medium">{ocrResult.total_pages}</p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Processed:</span>
                          <p className="font-medium">{ocrResult.processed_pages}</p>
                        </div>
                      </>
                    )}
                    {ocrResult.confidence && (
                      <div>
                        <span className="text-muted-foreground">Confidence:</span>
                        <p className="font-medium">{(ocrResult.confidence * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    <div>
                      <span className="text-muted-foreground">Tokens Used:</span>
                      <p className="font-medium">{ocrResult.total_tokens_used}</p>
                    </div>
                  </div>

                  {ocrResult.document_id && (
                    <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                      <p className="text-sm font-medium text-green-700 dark:text-green-300">
                        ✓ Saved to Knowledge Base
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                        Document ID: {ocrResult.document_id}
                      </p>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={handleDownloadText} variant="outline" size="sm" className="flex-1">
                      <Download className="mr-2 h-4 w-4" />
                      Download Text
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Extracted Text Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Extracted Text</CardTitle>
                </CardHeader>
                <CardContent>
                  {ocrResult.pages && ocrResult.pages.length > 1 ? (
                    <Tabs value={selectedPage.toString()} onValueChange={(v) => setSelectedPage(parseInt(v))}>
                      <TabsList className="w-full justify-start overflow-x-auto">
                        {ocrResult.pages.map((page) => (
                          <TabsTrigger key={page.page_number} value={page.page_number.toString()}>
                            Page {page.page_number}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                      {ocrResult.pages.map((page) => (
                        <TabsContent key={page.page_number} value={page.page_number.toString()}>
                          <ScrollArea className="h-[500px] w-full rounded-md border p-4">
                            <pre className="whitespace-pre-wrap text-sm font-mono">{page.extracted_text}</pre>
                          </ScrollArea>
                          <div className="mt-2 text-xs text-muted-foreground">
                            Confidence: {(page.confidence * 100).toFixed(1)}% | Tokens: {page.tokens_used}
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  ) : (
                    <ScrollArea className="h-[500px] w-full rounded-md border p-4">
                      <pre className="whitespace-pre-wrap text-sm font-mono">{ocrResult.extracted_text}</pre>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <FileText className="h-16 w-16 text-muted-foreground mb-4" />
                <p className="text-lg font-medium">No results yet</p>
                <p className="text-sm text-muted-foreground">
                  Upload a file and click &quot;Process OCR&quot; to extract text
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
