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
      contrastText: "#fff",
    },
    secondary: {
      light: "#FFF263",
      main: "#FBC02D",
      dark: "#C49000",
      contrastText: "#000",
    },
    success: { main: "#DCFCE7", contrastText: "#00A63E" },
    error: { main: "#FFE2E2", contrastText: "#82181A" },
    warning: { main: "#FFEDD4", contrastText: "#404040" },
    info: { main: "#DBEAFE", contrastText: "#1C398E" },
    contrastThreshold: 3,
    tonalOffset: 0.1,
  },
  typography: {
    button: {
      textTransform: "none",
    },
    fontFamily: [
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(","),
  },
  breakpoints: {
    values: {
      xs: 0, // smallest phones
      sm: 380, // typical modern phones portrait
      md: 600, // larger phones + small tablets / foldables
      lg: 1080, // tablets portrait / foldables expanded
      xl: 1280, // tablets landscape
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

export const MAP_BUTTON_GREY = "#7F7F7F";
export const LIGHT_GREY = "#DADADA";
export const INFO_PANEL_CONTENT_BACKGROUND = "#EEEEEE";
export const HEADER_GREY = "#BFBFBF";
