import { createTheme } from '@mui/material/styles'
import { GridCellParams, GridColumnHeaderParams } from '@mui/x-data-grid-pro'
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
    },
    fontFamily: "'BC Sans', 'Noto Sans', Verdana, Arial, sans-serif"
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
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          fontSize: '1em'
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

export const INFO_PANEL_HEADER_BACKGROUND = '#BFBFBF'
export const INFO_PANEL_CONTENT_BACKGROUND = '#EEEEEE'
export const TRANSPARENT_COLOUR = '#0000'

interface WeatherParams {
  [key: string]: {
    active: string
    inactive: string
    text: string
  }
}

export const MORECAST_WEATHER_PARAMS: WeatherParams = {
  temp: { active: 'rgba(215, 48, 39, 0.3)', inactive: 'rgba(215, 48, 39, 0.2)', text: 'black' },
  rh: { active: 'rgba(254, 224, 144, 0.7)', inactive: 'rgba(254, 224, 144, 0.3)', text: 'black' },
  windDirection: { active: 'rgba(145, 191, 219, 0.5)', inactive: 'rgba(145, 191, 219, 0.2)', text: 'black' },
  windSpeed: { active: 'rgba(69, 117, 180, 0.6)', inactive: 'rgba(69, 117, 180, 0.3)', text: 'black' },
  precip: { active: 'rgba(127, 191, 123, 0.4)', inactive: 'rgba(77, 146, 33, 0.1)', text: 'black' },
  gc: { active: 'rgba(153, 142, 195, 0.7)', inactive: 'rgba(153, 142, 195, 0.2)', text: 'black' },
  summary: { active: 'rgba(0, 51, 102, 1)', inactive: 'rgba(0, 51, 102, 0.6)', text: 'white' }
}
export type MoreCastParams = typeof MORECAST_WEATHER_PARAMS

interface ModelDetails {
  [key: string]: {
    bg: string
    border: string
  }
}
export const MORECAST_MODEL_COLORS: ModelDetails = {
  nam: { bg: 'rgba(255, 20, 147, 0.1)', border: 'rgba(255, 20, 147, 1)' },
  gfs: { bg: 'rgba(205, 133, 63, 0.1)', border: 'rgba(205, 133, 63, 1)' },
  gdps: { bg: 'rgba(0, 0, 255, 0.1)', border: 'rgba(0, 0, 255, 1)' },
  rdps: { bg: 'rgba(56, 152, 52, 0.1)', border: 'rgba(56, 152, 52, 1)' },
  hrdps: { bg: 'rgba(7, 79, 0, 0.1)', border: 'rgba(7, 79, 0, 1)' }
}
export type MoreCastModelColors = typeof MORECAST_MODEL_COLORS

export const modelColorClass = (params: Pick<GridCellParams | GridColumnHeaderParams, 'colDef' | 'field'>) => {
  if (params.field.includes('Actual')) {
    return ''
  }
  const stringKeys = Object.keys(MORECAST_MODEL_COLORS)
  const modelKey = stringKeys.find(key => params.colDef.headerName?.startsWith(key.toUpperCase()))
  return modelKey ? modelKey : ''
}

export const modelHeaderColorClass = (params: Pick<GridCellParams | GridColumnHeaderParams, 'colDef' | 'field'>) => {
  const modelClass = modelColorClass(params)
  return modelClass === '' ? modelClass : `${modelClass}-header`
}

// Theme for edited windspeed and precip cells in Fire Calc
export const adjustedTheme = createTheme({
  components: {
    MuiInputBase: {
      styleOverrides: {
        root: {
          border: '2px solid #460270',
          fontSize: '0.875rem'
        }
      }
    }
  }
})

interface FireWatchPrescriptionColorInterface {
  [key: string]: {
    bgcolor: string
    hover: string
  }
}
export const FireWatchPrescriptionColors: FireWatchPrescriptionColorInterface = {
  all: { bgcolor: '#e1f1df', hover: '#cddfc9' },
  hfi: { bgcolor: '#fef4cf', hover: '#fce9b3' },
  no: { bgcolor: '#ffffff', hover: '#ffffff' }
}