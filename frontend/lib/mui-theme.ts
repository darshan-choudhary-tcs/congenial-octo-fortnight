'use client';

import { createTheme, ThemeOptions } from '@mui/material/styles';

// Helper function to convert HSL to RGB for MUI
function hslToRgb(h: number, s: number, l: number): string {
  s /= 100;
  l /= 100;
  const k = (n: number) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) =>
    l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return `rgb(${Math.round(255 * f(0))}, ${Math.round(255 * f(8))}, ${Math.round(255 * f(4))})`;
}

// Material Design 3 Light Theme
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: hslToRgb(221.2, 83.2, 53.3), // --primary
      contrastText: hslToRgb(210, 40, 98), // --primary-foreground
    },
    secondary: {
      main: hslToRgb(210, 40, 96.1), // --secondary
      contrastText: hslToRgb(222.2, 47.4, 11.2), // --secondary-foreground
    },
    error: {
      main: hslToRgb(0, 84.2, 60.2), // --destructive
      contrastText: hslToRgb(210, 40, 98), // --destructive-foreground
    },
    warning: {
      main: hslToRgb(38, 92, 50),
      contrastText: hslToRgb(0, 0, 100),
    },
    info: {
      main: hslToRgb(199, 89, 48),
      contrastText: hslToRgb(0, 0, 100),
    },
    success: {
      main: hslToRgb(142, 71, 45),
      contrastText: hslToRgb(0, 0, 100),
    },
    background: {
      default: hslToRgb(0, 0, 100), // --background
      paper: hslToRgb(0, 0, 100), // --card
    },
    text: {
      primary: hslToRgb(222.2, 84, 4.9), // --foreground
      secondary: hslToRgb(215.4, 16.3, 46.9), // --muted-foreground
    },
    divider: hslToRgb(214.3, 31.8, 91.4), // --border
  },
  shape: {
    borderRadius: 12, // Material Design 3 uses softer corners
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none', // Material Design 3 prefers sentence case
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '10px 24px',
          fontSize: '0.875rem',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${hslToRgb(214.3, 31.8, 91.4)}`,
        },
      },
    },
  },
};

// Material Design 3 Dark Theme
const darkThemeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: {
      main: hslToRgb(217.2, 91.2, 59.8), // --primary (dark)
      contrastText: hslToRgb(222.2, 47.4, 11.2), // --primary-foreground (dark)
    },
    secondary: {
      main: hslToRgb(217.2, 32.6, 17.5), // --secondary (dark)
      contrastText: hslToRgb(210, 40, 98), // --secondary-foreground (dark)
    },
    error: {
      main: hslToRgb(0, 62.8, 50.6), // --destructive (dark) - adjusted for visibility
      contrastText: hslToRgb(210, 40, 98), // --destructive-foreground (dark)
    },
    warning: {
      main: hslToRgb(38, 92, 60),
      contrastText: hslToRgb(0, 0, 0),
    },
    info: {
      main: hslToRgb(199, 89, 58),
      contrastText: hslToRgb(0, 0, 0),
    },
    success: {
      main: hslToRgb(142, 71, 55),
      contrastText: hslToRgb(0, 0, 0),
    },
    background: {
      default: hslToRgb(222.2, 84, 4.9), // --background (dark)
      paper: hslToRgb(222.2, 84, 8), // --card (dark) - slightly lighter
    },
    text: {
      primary: hslToRgb(210, 40, 98), // --foreground (dark)
      secondary: hslToRgb(215, 20.2, 65.1), // --muted-foreground (dark)
    },
    divider: hslToRgb(217.2, 32.6, 17.5), // --border (dark)
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '10px 24px',
          fontSize: '0.875rem',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundImage: 'none', // Remove MUI's default gradient in dark mode
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${hslToRgb(217.2, 32.6, 17.5)}`,
        },
      },
    },
  },
};

export const lightTheme = createTheme(lightThemeOptions);
export const darkTheme = createTheme(darkThemeOptions);
