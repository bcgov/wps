import { createTheme } from "@mui/material/styles";
// Theme documentation: https://material-ui.com/customization/palette/
// Theme demo: https://material.io/resources/color/#!/?view.left=1&view.right=1&primary.color=003365&secondary.color=FBC02D
// Do not export this directly for styling! theme should be accessed within makeStyles & withStyles. Use ErrorMessage.tsx as a reference
export const theme = createTheme({
  palette: {
    primary: {
      light: "#3E5C93",
      main: "#003366",
      dark: "#000C3A",
      contrastText: "#fff"
    },
    secondary: {
      light: "#FFF263",
      main: "#FBC02D",
      dark: "#C49000",
      contrastText: "#000"
    },
    success: { main: "#2E8540" },
    error: { main: "#FF3E34" },
    warning: { main: "#FE7921" },
    contrastThreshold: 3,
    tonalOffset: 0.1,
  },
  typography: {
    button: {
      textTransform: "none",
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 1080, // Default: 960
      lg: 1280,
      xl: 1920,
    },
  },
  components: {
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: 14,
        },
      },
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          fontSize: "1em",
        },
      },
    },
  },
});

export const MAP_BUTTON_GREY = "#7F7F7F"