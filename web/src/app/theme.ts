import { createTheme } from '@mui/material/styles'
// Theme documentation: https://material-ui.com/customization/palette/
// Theme demo: https://material.io/resources/color/#!/?view.left=1&view.right=1&primary.color=003365&secondary.color=FBC02D
// Do not export this directly for styling! theme should be accessed within makeStyles & withStyles. Use ErrorMessage.tsx as a reference
export const theme = createTheme({
  palette: {
    primary: {
      light: '#3E5C93',
      main: '#003366',
      dark: '#000C3A'
    },
    secondary: {
      light: '#FFF263',
      main: '#FBC02D',
      dark: '#C49000'
    },
    success: { main: '#2E8540' },
    error: { main: '#FF3E34' },
    warning: { main: '#FE7921' },
    contrastThreshold: 3,
    tonalOffset: 0.1
  },
  typography: {
    button: {
      textTransform: 'none'
    }
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 1080, // Default: 960
      lg: 1280,
      xl: 1920
    }
  },
  components: {
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: 14
        }
      }
    }
  }
})

export const fireTableTheme = createTheme({
  ...theme,
  components: {
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: 2
        },
        head: {
          fontWeight: 'bold',
          minWidth: 30,
          padding: 1,
          paddingLeft: 7
        },
        stickyHeader: {
          padding: 5
        }
      }
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          fontSize: '1em'
        }
      }
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          padding: 0
        }
      }
    }
  }
})

export const BACKGROUND_COLOR = { backgroundColor: '#e9ecf5' }

export const LANDING_BACKGROUND_COLOUR = '#f2f2f2'

export const PLANNING_AREA = {
  minWidth: 45,
  minHeight: 45,
  height: 45
}
export const UNSELECTED_STATION_COLOR = 'rgba(0,0,0,0.54)'
export const DARK_GREY = '#A7A7A7'
export const LIGHT_GREY = '#DADADA'
export const MEDIUM_GREY = '#B5B5B5'

export const MORECAST_COLORS = {
  temp: 'rgba(215, 48, 39, 0.3)',
  rh: 'rgba(254, 224, 144, 0.7)',
  windDirection: 'rgba(145, 191, 219, 0.5)',
  windSpeed: 'rgba(69, 117, 180, 0.6)',
  precip: 'rgba(127, 191, 123, 0.4)',
  gc: 'rgba(153, 142, 195, 0.7)',
  summary: 'rgba(0, 51, 102, 1)'
}
