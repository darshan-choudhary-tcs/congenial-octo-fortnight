'use client';

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  FormControlLabel,
  Switch,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Grid,
  Divider,
  Container,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  Psychology as PsychologyIcon,
  Lightbulb as LightbulbIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckCircleIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import { councilAPI } from '@/lib/api';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useRouter } from 'next/navigation';

interface VoteResult {
  agent: string;
  response: string;
  confidence: number;
  reasoning: string;
  vote_weight: number;
  temperature: number;
}

interface CouncilResponse {
  response: string;
  voting_strategy: string;
  votes: VoteResult[];
  consensus_metrics: {
    consensus_level: number;
    confidence_variance: number;
    agreement_score: number;
    avg_confidence: number;
    min_confidence: number;
    max_confidence: number;
  };
  aggregated_confidence: number;
  synthesis_used: boolean;
  sources: any[];
  failed_votes: any[];
  debate_rounds: number;
  agents_involved: string[];
  execution_time: number;
  token_usage: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  provider: string;
}

const agentIcons = {
  AnalyticalVoter: <AnalyticsIcon />,
  CreativeVoter: <LightbulbIcon />,
  CriticalVoter: <PsychologyIcon />,
};

const agentColors = {
  AnalyticalVoter: '#2196f3',
  CreativeVoter: '#ff9800',
  CriticalVoter: '#9c27b0',
};

export default function CouncilPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [provider, setProvider] = useState('ollama');
  const [votingStrategy, setVotingStrategy] = useState('weighted_confidence');
  const [includeSynthesis, setIncludeSynthesis] = useState(true);
  const [debateRounds, setDebateRounds] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CouncilResponse | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await councilAPI.evaluate({
        query,
        provider,
        voting_strategy: votingStrategy,
        include_synthesis: includeSynthesis,
        debate_rounds: debateRounds,
      });

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute council voting');
      console.error('Council voting error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getAgreementLevel = (consensusLevel: number) => {
    if (consensusLevel >= 0.8) return 'High';
    if (consensusLevel >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header AppBar */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <IconButton edge="start" onClick={() => router.push('/dashboard')}>
            <HomeIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1, ml: 2 }}>
            <PsychologyIcon />
            <Typography variant="h6">Council of Agents</Typography>
          </Box>
          <ThemeToggle />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4, flexGrow: 1 }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Multi-agent consensus system with diverse perspectives and voting strategies
        </Typography>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" gutterBottom>
                    Query Input
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Enter your query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a complex question that benefits from multiple perspectives..."
                    sx={{ mb: 2 }}
                  />

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>LLM Provider</InputLabel>
                        <Select
                          value={provider}
                          onChange={(e) => setProvider(e.target.value)}
                          label="LLM Provider"
                        >
                          <MenuItem value="ollama">Ollama (Local)</MenuItem>
                          <MenuItem value="custom">Custom API</MenuItem>
                          <MenuItem value="mixed">Mixed Providers</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Voting Strategy</InputLabel>
                        <Select
                          value={votingStrategy}
                          onChange={(e) => setVotingStrategy(e.target.value)}
                          label="Voting Strategy"
                        >
                          <MenuItem value="weighted_confidence">Weighted by Confidence</MenuItem>
                          <MenuItem value="highest_confidence">Highest Confidence</MenuItem>
                          <MenuItem value="majority">Majority Vote</MenuItem>
                          <MenuItem value="synthesis">Synthesis</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  <Box sx={{ mt: 3, mb: 2 }}>
                    <Typography gutterBottom>Debate Rounds: {debateRounds}</Typography>
                    <Slider
                      value={debateRounds}
                      onChange={(_, value) => setDebateRounds(value as number)}
                      min={1}
                      max={5}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={includeSynthesis}
                        onChange={(e) => setIncludeSynthesis(e.target.checked)}
                      />
                    }
                    label="Enable Response Synthesis"
                  />

                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                    onClick={handleSubmit}
                    disabled={loading || !query.trim()}
                    sx={{ mt: 2 }}
                  >
                    {loading ? 'Executing Council...' : 'Execute Council Voting'}
                  </Button>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography variant="h6" gutterBottom>
                    About Council Voting
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Multiple AI agents with different perspectives evaluate your query and reach consensus.
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <AnalyticsIcon sx={{ color: agentColors.AnalyticalVoter, fontSize: 20 }} />
                      <Typography variant="subtitle2">Analytical Voter</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem', mb: 2 }}>
                      Logical reasoning & factual accuracy (Temp: 0.3)
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <LightbulbIcon sx={{ color: agentColors.CreativeVoter, fontSize: 20 }} />
                      <Typography variant="subtitle2">Creative Voter</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem', mb: 2 }}>
                      Innovative ideas & creative solutions (Temp: 0.9)
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <PsychologyIcon sx={{ color: agentColors.CriticalVoter, fontSize: 20 }} />
                      <Typography variant="subtitle2">Critical Voter</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                      Balanced critique & risk identification (Temp: 0.5)
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" gutterBottom>
                    Voting Strategies:
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.6 }}>
                    • <strong>Weighted:</strong> By confidence scores<br />
                    • <strong>Highest:</strong> Most confident agent<br />
                    • <strong>Majority:</strong> Most common response<br />
                    • <strong>Synthesis:</strong> Combined perspectives
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Display */}
        {error && (
          <Grid item xs={12}>
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          </Grid>
        )}

        {/* Results Section */}
        {result && (
          <>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      <CheckCircleIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'success.main' }} />
                      Council Response
                    </Typography>
                    <Chip
                      label={`${getAgreementLevel(result.consensus_metrics.consensus_level)} Agreement`}
                      color={getConfidenceColor(result.consensus_metrics.consensus_level)}
                      size="small"
                    />
                  </Box>

                  <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', mb: 2 }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.response}
                    </Typography>
                  </Paper>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Consensus Score
                      </Typography>
                      <Typography variant="h6">
                        {(result.consensus_metrics.consensus_level * 100).toFixed(0)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={result.consensus_metrics.consensus_level * 100}
                        color={getConfidenceColor(result.consensus_metrics.consensus_level)}
                        sx={{ mt: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Avg Confidence
                      </Typography>
                      <Typography variant="h6">
                        {(result.consensus_metrics.avg_confidence * 100).toFixed(0)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={result.consensus_metrics.avg_confidence * 100}
                        color={getConfidenceColor(result.consensus_metrics.avg_confidence)}
                        sx={{ mt: 0.5 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Execution Time
                      </Typography>
                      <Typography variant="h6">{result.execution_time.toFixed(2)}s</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Typography variant="caption" color="text.secondary">
                        Total Tokens
                      </Typography>
                      <Typography variant="h6">
                        {result.token_usage.total_tokens.toLocaleString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Individual Votes */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Individual Agent Votes
              </Typography>
              {result.votes.map((vote, index) => (
                <Accordion key={index} defaultExpanded={index === 0}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
                      <Box sx={{ color: agentColors[vote.agent as keyof typeof agentColors] }}>
                        {agentIcons[vote.agent as keyof typeof agentIcons]}
                      </Box>
                      <Typography sx={{ flexGrow: 1 }}>{vote.agent}</Typography>
                      <Chip
                        label={`${(vote.confidence * 100).toFixed(0)}% Confident`}
                        color={getConfidenceColor(vote.confidence)}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        Weight: {vote.vote_weight} | Temp: {vote.temperature}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Response:
                      </Typography>
                      <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', mb: 2 }}>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {vote.response}
                        </Typography>
                      </Paper>

                      <Typography variant="subtitle2" gutterBottom>
                        Reasoning:
                      </Typography>
                      <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
                        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                          {vote.reasoning}
                        </Typography>
                      </Paper>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Grid>

            {/* Metadata */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Execution Metadata
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Strategy
                      </Typography>
                      <Typography variant="body2">{result.voting_strategy}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Provider
                      </Typography>
                      <Typography variant="body2">{result.provider}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Synthesis Used
                      </Typography>
                      <Typography variant="body2">{result.synthesis_used ? 'Yes' : 'No'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Debate Rounds
                      </Typography>
                      <Typography variant="body2">{result.debate_rounds}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Agreement Score
                      </Typography>
                      <Typography variant="body2">
                        {(result.consensus_metrics.agreement_score * 100).toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Confidence Variance
                      </Typography>
                      <Typography variant="body2">
                        {result.consensus_metrics.confidence_variance.toFixed(3)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Min / Max Confidence
                      </Typography>
                      <Typography variant="body2">
                        {(result.consensus_metrics.min_confidence * 100).toFixed(0)}% / {(result.consensus_metrics.max_confidence * 100).toFixed(0)}%
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
      </Container>
    </Box>
  );
}
