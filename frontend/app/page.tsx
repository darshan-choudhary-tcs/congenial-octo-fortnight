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
import AnimatedStats from '@/components/AnimatedStats'
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
      icon: ZapIcon,
      title: 'Location-Based Renewable Analysis',
      description: 'Get tailored recommendations for solar, wind, hydro, and biomass based on your location and industry-specific energy needs.',
      color: 'primary.main',
    },
    {
      icon: BarChart3Icon,
      title: 'Cost-Optimized Portfolios',
      description: 'Balance cost, reliability, and sustainability goals with AI-powered energy mix optimization and price forecasting.',
      color: 'success.main',
    },
    {
      icon: BrainIcon,
      title: 'Council of Agents Consensus',
      description: 'Unique multi-agent voting system where 3 specialized AI agents debate and reach consensus for quality assurance.',
      color: 'secondary.main',
    },
    {
      icon: FileTextIcon,
      title: 'Historical Energy Analysis',
      description: 'Upload consumption data to identify patterns, anomalies, and optimization opportunities in your energy usage.',
      color: 'warning.main',
    },
    {
      icon: TargetIcon,
      title: 'ESG Goal Tracking',
      description: 'Monitor progress toward sustainability KPIs with renewable percentage tracking and zero non-renewable targets.',
      color: 'error.main',
    },
    {
      icon: MessageSquareIcon,
      title: 'Real-Time Energy Reports',
      description: 'Stream comprehensive energy portfolio recommendations with visual analytics and actionable insights.',
      color: 'info.main',
    },
  ]

  const useCases = [
    {
      icon: ZapIcon,
      title: 'Renewable Energy Planning',
      description: 'Determine the optimal mix of solar, wind, hydro, and biomass for your facility based on location and budget.',
    },
    {
      icon: TargetIcon,
      title: 'ESG Reporting & Compliance',
      description: 'Track renewable energy adoption, monitor sustainability KPIs, and generate compliance-ready reports.',
    },
    {
      icon: BarChart3Icon,
      title: 'Cost Reduction Analysis',
      description: 'Identify optimization opportunities in historical consumption data and reduce energy costs while increasing renewables.',
    },
  ]

  const benefits = [
    'Location-specific renewable potential analysis for 50+ Indian cities',
    'Multi-agent consensus system with democratic voting',
    'ESG-aligned portfolio optimization with cost-reliability balance',
    'Historical consumption pattern analysis and anomaly detection',
    'Real-time streaming energy reports with visual analytics',
    'Company-scoped knowledge base with energy metadata',
  ]

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Navigation */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
              flexGrow: 1,
              cursor: 'pointer'
            }}
            onClick={() => router.push('/')}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 40,
                height: 40,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                boxShadow: '0 4px 12px rgba(5, 150, 105, 0.4)'
              }}
            >
              <ZapIcon sx={{ fontSize: 24, color: 'white' }} />
            </Box>
            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  fontSize: '1.25rem',
                  background: 'linear-gradient(90deg, #059669 0%, #047857 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  lineHeight: 1.2
                }}
              >
                AERO
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.7rem',
                  display: 'block',
                  lineHeight: 1
                }}
              >
                Energy Intelligence Platform
              </Typography>
            </Box>
          </Box>
          <Stack direction="row" spacing={{ xs: 1, sm: 2 }} alignItems="center">
            <ThemeToggle />
            <Button
              variant="text"
              onClick={() => router.push('/auth/login')}
              sx={{
                color: 'text.primary',
                fontWeight: 600,
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }}
            >
              Sign In
            </Button>
            <Button
              variant="contained"
              endIcon={<ArrowRightIcon />}
              onClick={() => router.push('/auth/register')}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                px: 3,
                bgcolor: '#059669',
                color: 'white',
                boxShadow: '0 4px 12px rgba(5, 150, 105, 0.4)',
                '&:hover': {
                  bgcolor: '#047857',
                  boxShadow: '0 6px 16px rgba(5, 150, 105, 0.5)'
                }
              }}
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
              label="AI-Powered Energy Intelligence"
              variant="outlined"
              sx={{ mb: 3, borderColor: '#059669', color: '#059669' }}
            />
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', md: '3.75rem' },
                fontWeight: 700,
                mb: 3,
                background: 'linear-gradient(90deg, #059669 0%, #047857 50%, #065f46 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              Optimize Your Energy Mix with
              <br />
              AI-Powered Sustainability Intelligence
            </Typography>
            <Typography
              variant="h5"
              color="text.secondary"
              sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}
            >
              Make smarter renewable energy decisions with location-specific insights, cost optimization,
              and ESG-aligned recommendations powered by our unique multi-agent consensus system.
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
                  px: 4,
                  bgcolor: '#059669',
                  color: 'white',
                  '&:hover': {
                    bgcolor: '#047857'
                  }
                }}
              >
                Start Energy Assessment
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => router.push('/auth/login')}
                sx={{
                  px: 4,
                  borderColor: '#059669',
                  color: '#059669',
                  '&:hover': {
                    borderColor: '#047857',
                    bgcolor: 'rgba(5, 150, 105, 0.04)'
                  }
                }}
              >
                Sign In
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
              Energy Intelligence Features
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
              Comprehensive tools to optimize your renewable energy strategy and achieve sustainability goals
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

      {/* Animated Statistics */}
      <AnimatedStats />

      {/* Use Cases */}
      <Box sx={{ py: 10, px: 2, bgcolor: 'background.default' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h2" sx={{ fontWeight: 700, mb: 2 }}>
              Built for Energy Professionals
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
              From sustainability officers to energy managers, optimize your renewable strategy with AI
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
                Why Choose AERO?
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
                Purpose-built for renewable energy optimization with specialized agents, location-based
                intelligence, and transparent AI decision-making you can trust.
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
                  background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                  color: 'white'
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 2, color: 'white' }}>
                    Ready to Optimize Your Energy?
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 4, color: 'rgba(255,255,255,0.9)' }}>
                    Join organizations already using AERO to achieve their sustainability goals
                  </Typography>
                  <Stack spacing={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <TargetIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          50+
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          Indian Locations Supported
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <ZapIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          4
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          Renewable Sources Analyzed
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <BrainIcon sx={{ fontSize: 28 }} />
                      </Paper>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'white' }}>
                          3
                        </Typography>
                        <Typography sx={{ color: 'rgba(255,255,255,0.8)' }}>
                          AI Agents in Council
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
                        color: '#059669',
                        '&:hover': {
                          bgcolor: 'rgba(255,255,255,0.9)',
                          color: '#047857'
                        }
                      }}
                    >
                      Start Energy Assessment
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
          background: 'linear-gradient(90deg, #059669 0%, #047857 100%)',
          color: 'white'
        }}
      >
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h2" sx={{ fontWeight: 700, mb: 3, color: 'white' }}>
              Ready to Achieve Your Sustainability Goals?
            </Typography>
            <Typography variant="h6" sx={{ mb: 4, color: 'rgba(255,255,255,0.9)' }}>
              Start optimizing your renewable energy mix with AI-powered insights.
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
                  color: '#059669',
                  px: 4,
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.9)',
                    color: '#047857'
                  }
                }}
              >
                Start Energy Assessment
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
                <ZapIcon sx={{ fontSize: 28, color: '#059669' }} />
                <Typography sx={{ fontWeight: 700, color: 'white' }}>
                  AERO: AI for Energy Resource Optimization
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: 'grey.500' }}>
                AI-powered platform for renewable energy optimization and sustainability intelligence.
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
              &copy; {new Date().getFullYear()} AERO: AI for Energy Resource Optimization. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}
