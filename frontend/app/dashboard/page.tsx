'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  AppBar,
  Toolbar,
  Stack,
  Paper,
  CircularProgress,
  Alert,
  Skeleton,
  Chip,
  IconButton,
  Menu,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material'
import { useSnackbar } from '@/components/SnackbarProvider'
import { ThemeToggle } from '@/components/ThemeToggle'
import {
  Psychology as BrainIcon,
  Description as FileTextIcon,
  Chat as MessageSquareIcon,
  Group as UsersIcon,
  BarChart as BarChart3Icon,
  Logout as LogOutIcon,
  Code as CodeIcon,
  Home as HomeIcon,
  TrendingUp as TrendingUpIcon,
  Lightbulb as LightbulbIcon,
  AttachMoney as MoneyIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  CalendarMonth as CalendarIcon,
  Folder as FolderIcon,
  EnergySavingsLeaf as LeafIcon,
  Settings as SettingsIcon,
  Key as KeyIcon
} from '@mui/icons-material'
import { authAPI, profileAPI } from '@/lib/api'
import CountUp from 'react-countup'
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

interface ProfileData {
  id: number
  user_id: number
  industry: string
  location: string
  sustainability_target_kp1: number
  sustainability_target_kp2: number
  budget: number
  historical_data_path: string | null
  created_at: string
  updated_at: string
}

interface HistoricalData {
  total_renewable_kwh: number
  total_non_renewable_kwh: number
  renewable_percentage: number
  non_renewable_percentage: number
  total_cost_inr: number
  average_unit_price_inr: number
  total_energy_required_kwh: number
  monthly_data: any[]
  energy_mix: Record<string, number>
  provider_distribution: any[]
  start_date: string
  end_date: string
  total_records: number
}

export default function DashboardPage() {
  const { user, logout, hasPermission, hasRole, refreshUser } = useAuth()
  const router = useRouter()
  const { showSnackbar } = useSnackbar()
  const [updatingProvider, setUpdatingProvider] = useState(false)
  const [updatingExplainability, setUpdatingExplainability] = useState(false)
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null)
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // New state for profile and historical data
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [historicalData, setHistoricalData] = useState<HistoricalData | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [loadingHistorical, setLoadingHistorical] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [historicalError, setHistoricalError] = useState('')

  // Fetch profile and historical data
  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        setLoadingProfile(true)
        const response = await profileAPI.getProfile()
        setProfile(response.data)
        setProfileError('')

        // If historical data exists, fetch it
        if (response.data.historical_data_path) {
          setLoadingHistorical(true)
          try {
            const histResponse = await profileAPI.getHistoricalData({ aggregation: 'monthly' })
            setHistoricalData(histResponse.data)
            setHistoricalError('')
          } catch (err: any) {
            console.error('Error fetching historical data:', err)
            setHistoricalError(err.response?.data?.detail || 'Failed to load historical data')
          } finally {
            setLoadingHistorical(false)
          }
        }
      } catch (err: any) {
        console.error('Error fetching profile:', err)
        setProfileError(err.response?.data?.detail || 'Failed to load profile')
      } finally {
        setLoadingProfile(false)
      }
    }

    if (user) {
      fetchProfileData()
    }
  }, [user])

  const features = [
    {
      title: 'Chat',
      description: 'Interact with AI using RAG and multi-agent system',
      icon: MessageSquareIcon,
      href: '/dashboard/chat',
      permission: 'chat:use',
      color: 'primary.main',
    },
    {
      title: 'Reports',
      description: 'Energy analysis reports with multi-agent optimization',
      icon: BarChart3Icon,
      href: '/dashboard/reports',
      permission: 'reports:generate',
      color: 'success.main',
    },
    {
      title: 'Saved Reports',
      description: 'View, export, and manage your saved energy reports',
      icon: FolderIcon,
      href: '/dashboard/saved-reports',
      permission: 'reports:view_saved',
      color: 'info.main',
    },
    // {
    //   title: 'Council of Agents',
    //   description: 'Multi-agent consensus with diverse AI perspectives',
    //   icon: BrainIcon,
    //   href: '/dashboard/council',
    //   permission: 'chat:use',
    //   color: 'secondary.main',
    // },
    // {
    //   title: 'Explainability',
    //   description: 'View AI reasoning and confidence scores',
    //   icon: BarChart3Icon,
    //   href: '/dashboard/explainability',
    //   permission: 'explain:view',
    //   color: 'warning.main',
    // },
    {
      title: 'Admin Panel',
      description: 'Manage users, roles, and system settings',
      icon: UsersIcon,
      href: '/dashboard/admin',
      roles: ['admin', 'super_admin'],
      color: 'error.main',
    },
  ]

  const accessibleFeatures = features.filter((feature) => {
    if ('roles' in feature && feature.roles) return feature.roles.some((role: string) => hasRole(role))
    if (feature.permission) return hasPermission(feature.permission)
    return true
  })

  // Chart colors
  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  const energyMixColors: Record<string, string> = {
    Solar: '#f59e0b',
    Wind: '#3b82f6',
    Hydro: '#10b981',
    Coal: '#6b7280'
  }

  const handleUpdateProvider = async (value: string) => {
    setUpdatingProvider(true)
    try {
      await authAPI.updateProfile({ preferred_llm: value })
      await refreshUser()
      showSnackbar(`LLM provider changed to ${value}`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update provider', 'error')
    } finally {
      setUpdatingProvider(false)
    }
  }

  const handleUpdateExplainability = async (value: string) => {
    setUpdatingExplainability(true)
    try {
      await authAPI.updateProfile({ explainability_level: value })
      await refreshUser()
      showSnackbar(`Detail level changed to ${value}`, 'success')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to update explainability level', 'error')
    } finally {
      setUpdatingExplainability(false)
    }
  }

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword || !confirmPassword) {
      showSnackbar('Please fill in all fields', 'warning')
      return
    }

    if (newPassword.length < 6) {
      showSnackbar('New password must be at least 6 characters', 'warning')
      return
    }

    if (newPassword !== confirmPassword) {
      showSnackbar('New passwords do not match', 'warning')
      return
    }

    try {
      await authAPI.changePassword(oldPassword, newPassword)
      showSnackbar('Password changed successfully', 'success')
      setShowPasswordDialog(false)
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to change password', 'error')
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }} elevation={1}>
        <Container maxWidth="xl">
          <Box sx={{ py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HomeIcon color="primary" />
                <Typography variant="h5" fontWeight="bold">
                  Dashboard
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {user?.full_name || user?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                  {user?.roles.join(', ')}
                </Typography>
              </Box>
              <ThemeToggle />
              <IconButton
                size="small"
                onClick={(e) => setSettingsAnchor(e.currentTarget)}
              >
                <SettingsIcon />
              </IconButton>
              <Menu
                anchorEl={settingsAnchor}
                open={Boolean(settingsAnchor)}
                onClose={() => setSettingsAnchor(null)}
              >
                <MenuItem
                  onClick={() => {
                    setSettingsAnchor(null)
                    setShowPasswordDialog(true)
                  }}
                >
                  <KeyIcon sx={{ mr: 1, fontSize: 20 }} />
                  Change Password
                </MenuItem>
              </Menu>
              <Button
                variant="outlined"
                size="small"
                startIcon={<LogOutIcon />}
                onClick={logout}
              >
                Logout
              </Button>
            </Box>
          </Box>
        </Container>
      </Paper>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
            Company Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your sustainability KPIs and energy consumption data
          </Typography>
        </Box>

        {/* Error Messages */}
        {profileError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {profileError}
          </Alert>
        )}

        {/* Company Profile & KPIs Section */}
        {loadingProfile ? (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Skeleton variant="rectangular" height={140} sx={{ borderRadius: 2 }} />
              </Grid>
            ))}
          </Grid>
        ) : profile ? (
          <>
            {/* KPI Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Company Info */}
              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <BusinessIcon sx={{ color: 'white' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
                        Industry
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: 'white', mb: 1 }}>
                      {profile.industry}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      Sector classification
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <LocationIcon sx={{ color: 'white' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
                        Location
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: 'white', mb: 1 }}>
                      {profile.location}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      Operating region
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <MoneyIcon sx={{ color: 'white' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
                        Annual Budget
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: 'white', mb: 1 }}>
                      <CountUp end={profile.budget} duration={2} separator="," prefix="₹" />
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      Sustainability initiatives
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <CalendarIcon sx={{ color: 'white' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
                        Target Year (KP1)
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: 'white', mb: 1 }}>
                      {profile.sustainability_target_kp1}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      Zero non-renewable goal
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <TrendingUpIcon sx={{ color: 'white' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600, color: 'white' }}>
                        Renewable Target (KP2)
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: 'white', mb: 1 }}>
                      <CountUp end={profile.sustainability_target_kp2} duration={2} decimals={1} suffix="%" />
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      Renewable mix increase
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <LeafIcon sx={{ color: '#10b981' }} />
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        Current Renewable %
                      </Typography>
                    </Box>
                    {loadingHistorical ? (
                      <Skeleton width={80} height={48} />
                    ) : historicalData ? (
                      <>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981', mb: 1 }}>
                          <CountUp end={historicalData.renewable_percentage} duration={2} decimals={1} suffix="%" />
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          From historical data
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No data available
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Historical Data Visualizations */}
            {historicalData && (
              <>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
                  Historical Energy Data Analysis
                </Typography>

                {historicalError && (
                  <Alert severity="warning" sx={{ mb: 3 }}>
                    {historicalError}
                  </Alert>
                )}

                <Grid container spacing={3} sx={{ mb: 4 }}>
                  {/* Energy Mix Pie Chart */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                          Energy Source Mix
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={Object.entries(historicalData.energy_mix).map(([name, value]) => ({
                                name,
                                value
                              }))}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(1)}%`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {Object.keys(historicalData.energy_mix).map((key, index) => (
                                <Cell key={`cell-${index}`} fill={energyMixColors[key] || COLORS[index]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value: number) => `${value.toFixed(2)} kWh`} />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Summary Stats */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                          Energy Summary
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Total Energy
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {historicalData.total_energy_required_kwh.toLocaleString()} kWh
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Total Cost
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              ₹{historicalData.total_cost_inr.toLocaleString()}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Renewable
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600, color: '#10b981' }}>
                              {historicalData.total_renewable_kwh.toLocaleString()} kWh
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Non-Renewable
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600, color: '#ef4444' }}>
                              {historicalData.total_non_renewable_kwh.toLocaleString()} kWh
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              Average Unit Price
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              ₹{historicalData.average_unit_price_inr.toFixed(2)}/kWh
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                              Data Period: {historicalData.start_date} to {historicalData.end_date}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Monthly Energy Consumption Trend */}
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                          Monthly Energy Consumption Trends
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={historicalData.monthly_data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line
                              type="monotone"
                              dataKey="renewable_kwh"
                              stroke="#10b981"
                              strokeWidth={2}
                              name="Renewable (kWh)"
                            />
                            <Line
                              type="monotone"
                              dataKey="non_renewable_kwh"
                              stroke="#ef4444"
                              strokeWidth={2}
                              name="Non-Renewable (kWh)"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Monthly Cost Trend */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                          Monthly Cost Analysis
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={historicalData.monthly_data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis />
                            <Tooltip />
                            <Area
                              type="monotone"
                              dataKey="total_cost_inr"
                              stroke="#3b82f6"
                              fill="#3b82f6"
                              fillOpacity={0.6}
                              name="Total Cost (INR)"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Renewable Percentage Trend */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                          Renewable Energy Percentage
                        </Typography>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={historicalData.monthly_data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="renewable_percentage" fill="#10b981" name="Renewable %" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </>
            )}

            {!historicalData && !loadingHistorical && (
              <Alert severity="info" sx={{ mb: 4 }}>
                No historical energy data available. Upload historical data during setup to see detailed analytics.
              </Alert>
            )}
          </>
        ) : null}

        {/* Quick Access Features */}
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, mt: 6 }}>
          Quick Access
        </Typography>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {accessibleFeatures.slice(0, 6).map((feature) => {
            const Icon = feature.icon
            return (
              <Grid item xs={12} sm={6} md={4} key={feature.href}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 6
                    }
                  }}
                  onClick={() => router.push(feature.href)}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 1.5,
                          bgcolor: 'action.hover',
                          borderRadius: 2
                        }}
                      >
                        <Icon sx={{ fontSize: 28, color: feature.color }} />
                      </Paper>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {feature.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {feature.description}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      </Container>

      {/* Password Change Dialog */}
      <Dialog
        open={showPasswordDialog}
        onClose={() => setShowPasswordDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Current Password"
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
            />
            <TextField
              fullWidth
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              helperText="Password must be at least 6 characters"
            />
            <TextField
              fullWidth
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={!oldPassword || !newPassword || !confirmPassword || newPassword.length < 6}
          >
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
