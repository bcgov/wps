import { createMuiTheme } from '@material-ui/core/styles'

/**
 * Theme documentation: https://material-ui.com/customization/palette/
 * Theme demo: https://material.io/resources/color/#!/?view.left=1&view.right=1&primary.color=003365&secondary.color=FBC02D
 */

const theme = createMuiTheme({
  palette: {
    primary: {
      light: '#3e5c93',
      main: '#003365',
      dark: '#000c3a'
    },
    secondary: {
      light: '#fff263',
      main: '#fbc02d',
      dark: '#c49000'
    },
    success: { main: '#44D77A' },
    error: { main: '#FF3E34' },
    warning: { main: '#FE7921' },
    contrastThreshold: 3,
    tonalOffset: 0.1
  }
})

export default theme
