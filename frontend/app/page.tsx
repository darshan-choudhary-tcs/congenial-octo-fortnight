'use client'

import { useRouter } from 'next/navigation'
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  AppBar,
  Toolbar,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper
} from '@mui/material'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  Psychology as BrainIcon,
  Chat as MessageSquareIcon,
  Description as FileTextIcon,
  BarChart as BarChart3Icon,
  Security as ShieldIcon,
  Bolt as ZapIcon,
  Group as UsersIcon,
  ArrowForward as ArrowRightIcon,
  CheckCircle as CheckCircleIcon,
  AutoAwesome as SparklesIcon,
  GpsFixed as TargetIcon,
  Layers as LayersIcon
} from '@mui/icons-material'

export default function LandingPage() {
  const router = useRouter()

  const features = [
    {
      icon: BrainIcon,
      title: 'AI-Powered Intelligence',
      description: 'Advanced multi-agent system with RAG capabilities for intelligent document analysis and question answering.',
      color: 'primary.main',
    },
    {
      icon: MessageSquareIcon,
      title: 'Interactive Chat',
      description: 'Natural conversations with AI that understands context and provides accurate, grounded responses.',
      color: 'success.main',
    },
    {
      icon: FileTextIcon,
      title: 'Document Management',
      description: 'Upload and organize PDFs, text files, and documents into a searchable knowledge base.',
      color: 'secondary.main',
    },
    {
      icon: BarChart3Icon,
      title: 'Explainable AI',
      description: 'Understand how AI makes decisions with confidence scores, reasoning chains, and source attribution.',
      color: 'warning.main',
    },
    {
      icon: ShieldIcon,
      title: 'Role-Based Access',
      description: 'Enterprise-grade security with granular permissions and user role management.',
      color: 'error.main',
    },
    {
      icon: ZapIcon,
      title: 'Dual LLM Support',
      description: 'Choose between custom API endpoints or local Ollama models for flexibility and control.',
      color: 'info.main',
    },
  ]

  const useCases = [
    {
      icon: TargetIcon,
      title: 'Research & Analysis',
      description: 'Quickly analyze large document collections and extract insights with AI assistance.',
    },
    {
      icon: UsersIcon,
      title: 'Team Collaboration',
      description: 'Share knowledge across teams with organized document repositories and chat history.',
    },
    {
      icon: LayersIcon,
      title: 'Enterprise Integration',
      description: 'Integrate with existing workflows using flexible API endpoints and authentication.',
    },
  ]

  const benefits = [
    'Real-time document processing and embedding',
    'Multi-agent orchestration for complex queries',
    'Source attribution and grounding evidence',
    'Confidence scoring for AI responses',
    'Customizable explainability levels',
    'Admin dashboard for user management',
  ]

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Navigation */}
      <AppBar
        position="fixed"
        sx={{
          backgroundColor: 'background.paper',
          backdropFilter: 'blur(10px)',
          boxShadow: 1
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
            <BrainIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(90deg, #2563eb 0%, #4f46e5 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              AI RAG Platform
            </Typography>
          </Box>
          <Stack direction="row" spacing={2} alignItems="center">
            <ThemeToggle />
            <Button
              variant="text"
              onClick={() => router.push('/auth/login')}
            >
              Login
            </Button>
            <Button
              variant="contained"
              endIcon={<ArrowRightIcon />}
              onClick={() => router.push('/auth/register')}
            >
              Get Started
            </Button>
          </Stack>
        </Toolbar>
      </AppBar>

      {/* Hero Section */}
      <Box sx={{ pt: 16, pb: 10, px: 2, bgcolor: 'background.default' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center' }}>
            <Chip
              icon={<SparklesIcon />}
              label="Next Generation AI Platform"
              variant="outlined"
              sx={{ mb: 3 }}
            />
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', md: '3.75rem' },
                fontWeight: 700,
                mb: 3,
                background: 'linear-gradient(90deg, #2563eb 0%, #4f46e5 50%, #7c3aed 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Transform Documents into
              <br />
              Intelligent Conversations
            </Typography>
            <Typography
              variant="h5"
              color="text.secondary"
              sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}
            >
              Harness the power of Retrieval-Augmented Generation and multi-agent systems to unlock insights
              from your documents with explainable AI you can trust.
            </Typography>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={2}
              justifyContent="center"
            >
              <Button
                variant="contained"
                size="large"
                endIcon={<ArrowRightIcon />}
                onClick={() => router.push('/auth/register')}
                sx={{ px: 4 }}
              >
                Start Free Trial
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => router.push('/auth/login')}
                sx={{ px: 4 }}
              >
                View Demo
              </Button>
            </Stack>
          </Box>
        </Container>
      </Box>

      {/* Features Grid */}
      <Box sx={{ py: 10, px: 2, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h2" sx={{ fontWeight: 700, mb: 2 }}>
              Powerful Features
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
              Everything you need to build intelligent, document-powered AI applications
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'box-shadow 0.3s',
                    '&:hover': {
                      boxShadow: 6
                    }
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 1,
                          bgcolor: 'action.hover',
                          borderRadius: 2
                        }}
                      >
                        <feature.icon sx={{ fontSize: 28, color: feature.color }} />
                      </Paper>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {feature.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Use Cases */}
      <Box sx={{ py: 10, px: 2, bgcolor: 'background.default' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h2" sx={{ fontWeight: 700, mb: 2 }}>
              Built for Every Use Case
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
              From research teams to enterprise deployments, our platform scales with your needs
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {useCases.map((useCase, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    textAlign: 'center',
                    transition: 'box-shadow 0.3s',
                    '&:hover': {
                      boxShadow: 6
                    }
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        mx: 'auto',
                        mb: 3,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <useCase.icon sx={{ fontSize: 40, color: 'primary.main' }} />
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                      {useCase.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {useCase.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Benefits Section */}
      <Box sx={{ py: 10, px: 2, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} lg={6}>
              <Typography variant="h2" sx={{ fontWeight: 700, mb: 3 }}>
                Why Choose Our Platform?
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
                Built with the latest AI technologies and best practices, our platform delivers
                reliable, explainable results you can depend on.
              </Typography>
              <List>
                {benefits.map((benefit, index) => (
                  <ListItem key={index} disableGutters>
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      <CheckCircleIcon sx={{ color: 'success.main', fontSize: 28 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={benefit}
                      primaryTypographyProps={{
                        variant: 'body1',
                        sx: { fontWeight: 500 }
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
            <Grid item xs={12} lg={6}>
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)',
                  color: 'white'
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 2, color: 'white' }}>
                    Ready to Get Started?
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 4, color: 'rgba(255,255,255,0.9)' }}>
                    Join teams already using our platform to transform their document workflows
                  </Typography>
                  <Stack spacing={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <UsersIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          10,000+
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          Active Users
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <FileTextIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          1M+
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          Documents Processed
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <MessageSquareIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          5M+
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          Queries Answered
                        </Typography>
                      </Box>
                    </Box>
                    <Button
                      variant="contained"
                      size="large"
                      fullWidth
                      endIcon={<ArrowRightIcon />}
                      onClick={() => router.push('/auth/register')}
                      sx={{
                        bgcolor: 'white',
                        color: 'primary.main',
                        '&:hover': {
                          bgcolor: 'rgba(255,255,255,0.9)'
                        }
                      }}
                    >
                      Create Free Account
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          py: 10,
          px: 2,
          background: 'linear-gradient(90deg, #2563eb 0%, #4f46e5 100%)',
          color: 'white'
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h2" sx={{ fontWeight: 700, mb: 3, color: 'white' }}>
              Ready to Transform Your Documents?
            </Typography>
            <Typography variant="h6" sx={{ mb: 4, color: 'rgba(255,255,255,0.9)' }}>
              Start your journey with intelligent document processing today.
              No credit card required.
            </Typography>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={2}
              justifyContent="center"
            >
              <Button
                variant="contained"
                size="large"
                endIcon={<ArrowRightIcon />}
                onClick={() => router.push('/auth/register')}
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  px: 4,
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.9)'
                  }
                }}
              >
                Get Started Free
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => router.push('/auth/login')}
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  px: 4,
                  '&:hover': {
                    borderColor: 'white',
                    bgcolor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                Sign In
              </Button>
            </Stack>
          </Box>
        </Container>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 6,
          px: 2,
          bgcolor: 'grey.900',
          color: 'grey.400'
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} sx={{ mb: 4 }}>
            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <BrainIcon sx={{ fontSize: 28, color: 'primary.light' }} />
                <Typography sx={{ fontWeight: 700, color: 'white' }}>
                  AI RAG Platform
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: 'grey.500' }}>
                Next-generation AI platform for intelligent document processing and analysis.
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography sx={{ fontWeight: 600, color: 'white', mb: 2 }}>
                Product
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Features
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Pricing
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Documentation
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  API Reference
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography sx={{ fontWeight: 600, color: 'white', mb: 2 }}>
                Company
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  About Us
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Blog
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Careers
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Contact
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography sx={{ fontWeight: 600, color: 'white', mb: 2 }}>
                Legal
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Privacy Policy
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Terms of Service
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Security
                </Typography>
                <Typography variant="body2" component="a" href="#" sx={{ color: 'grey.400', textDecoration: 'none', '&:hover': { color: 'white' } }}>
                  Compliance
                </Typography>
              </Stack>
            </Grid>
          </Grid>
          <Box sx={{ borderTop: '1px solid', borderColor: 'grey.800', pt: 4, textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: 'grey.500' }}>
              &copy; {new Date().getFullYear()} AI RAG Platform. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
