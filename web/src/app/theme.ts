import { createStyles, createTheme } from '@material-ui/core/styles'
// Theme documentation: https://material-ui.com/customization/palette/
// Theme demo: https://material.io/resources/color/#!/?view.left=1&view.right=1&primary.color=003365&secondary.color=FBC02D
// Do not export this directly for styling! theme should be accessed within makeStyles & withStyles. Use ErrorMessage.tsx as a reference
export const theme = createTheme({
  palette: {
    primary: {
      light: '#3E5C93',
      main: '#003365',
      dark: '#000C3A'
    },
    secondary: {
      light: '#FFF263',
      main: '#FBC02D',
      dark: '#C49000'
    },
    success: { main: '#44D77A' },
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
  }
})

export const fireTableTheme = createTheme({
  ...theme,
  overrides: {
    MuiTableCell: {
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
        padding: 8
      }
    },
    MuiInputBase: {
      root: {
        fontSize: '1em'
      }
    },
    MuiOutlinedInput: {
      root: {
        padding: 0
      }
    }
  }
})

const BACKGROUND_COLOR = { backgroundColor: 'rgba(40, 53, 147, 0.05)' }
export const UNSELECTED_STATION_COLOR = 'rgba(0,0,0,0.54)'
export const fireTableStyles = createStyles({
  defaultBackground: BACKGROUND_COLOR,
  planningArea: { ...BACKGROUND_COLOR, width: 45, height: 45 },
  unselectedStation: { color: UNSELECTED_STATION_COLOR },
  controls: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'baseline'
  },
  fireCentre: {
    width: 45,
    height: 45,
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#dbd9d9'
  },
  sectionSeperatorBorder: {
    borderLeft: '1px solid #C4C4C4'
  },
  calculatedPlanningCell: {
    fontWeight: 'bold',
    textAlign: 'center',
    width: 30
  }
})
