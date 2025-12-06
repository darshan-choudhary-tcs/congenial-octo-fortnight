'use client'

import { Box, Container, Typography, Card, CardContent, Grid } from '@mui/material'
import CountUp from 'react-countup'
import {
  Description as DocumentIcon,
  QuestionAnswer as QueryIcon,
  People as PeopleIcon,
  CheckCircle as ConfidenceIcon,
  DataObject as VectorIcon,
  SmartToy as AgentIcon,
  Speed as SpeedIcon,
  Settings as SettingsIcon,
  LocationOn as LocationIcon,
  Bolt as EnergyIcon,
  EmojiObjects as RenewableIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material'
import statsData from '@/data/stats.json'

interface StatCardProps {
  icon: React.ReactNode
  value: number
  suffix: string
  label: string
  delay: number
  decimals?: number
  iconColor: string
}

interface StatData {
  icon: string
  value: number
  suffix: string
  label: string
  delay: number
  decimals: number
  iconColor: string
}

interface StatsConfig {
  stats: StatData[]
}

const StatCard = ({ icon, value, suffix, label, delay, decimals = 0, iconColor }: StatCardProps) => {
  return (
    <Card
      sx={{
        bgcolor: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        transition: 'all 0.3s ease-in-out',
        height: '100%',
        '&:hover': {
          transform: 'translateY(-8px)',
          boxShadow: 6,
          bgcolor: 'rgba(255, 255, 255, 0.15)',
        },
      }}
    >
      <CardContent sx={{ textAlign: 'center', py: 4 }}>
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: iconColor,
            mb: 2,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}
        >
          <Box sx={{ color: 'white', fontSize: 32 }}>
            {icon}
          </Box>
        </Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            mb: 1,
            color: 'white',
            letterSpacing: '-0.02em',
          }}
        >
          <CountUp
            end={value}
            duration={2.5}
            separator=","
            suffix={suffix}
            decimals={decimals}
            enableScrollSpy
            scrollSpyOnce
            scrollSpyDelay={delay}
            useEasing
          />
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'rgba(255, 255, 255, 0.8)',
            fontWeight: 500,
          }}
        >
          {label}
        </Typography>
      </CardContent>
    </Card>
  )
}

export default function AnimatedStats() {
  // Icon mapping to convert string names to components
  const iconMap: Record<string, React.ReactNode> = {
    DocumentIcon: <DocumentIcon fontSize="inherit" />,
    QueryIcon: <QueryIcon fontSize="inherit" />,
    PeopleIcon: <PeopleIcon fontSize="inherit" />,
    ConfidenceIcon: <ConfidenceIcon fontSize="inherit" />,
    VectorIcon: <VectorIcon fontSize="inherit" />,
    AgentIcon: <AgentIcon fontSize="inherit" />,
    SpeedIcon: <SpeedIcon fontSize="inherit" />,
    SettingsIcon: <SettingsIcon fontSize="inherit" />,
    LocationIcon: <LocationIcon fontSize="inherit" />,
    EnergyIcon: <EnergyIcon fontSize="inherit" />,
    RenewableIcon: <RenewableIcon fontSize="inherit" />,
    ReportIcon: <ReportIcon fontSize="inherit" />,
  }

  // Map JSON data to include React icon components
  const configData = statsData as StatsConfig
  const stats = configData.stats.map((stat: StatData) => ({
    ...stat,
    icon: iconMap[stat.icon] || <DocumentIcon fontSize="inherit" />,
  }))

  return (
    <Box
      sx={{
        py: 10,
        px: 2,
        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)',
          pointerEvents: 'none',
        },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              mb: 2,
              color: 'white',
              textShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
            }}
          >
            Built for Energy Optimization at Scale
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'rgba(255, 255, 255, 0.9)',
              maxWidth: 700,
              mx: 'auto',
              fontWeight: 400,
            }}
          >
            Advanced AI capabilities designed specifically for renewable energy intelligence
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {stats.map((stat: StatCardProps, index: number) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <StatCard {...stat} />
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  )
}
