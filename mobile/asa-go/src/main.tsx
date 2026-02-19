import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline, GlobalStyles } from "@mui/material";
import { ThemeProvider, StyledEngineProvider } from "@mui/material/styles";
import { Provider } from "react-redux";
import { store } from "@/store";
import { theme } from "@/theme.ts";
import App from "@/App.tsx";
import AuthWrapper from "@/components/AuthWrapper";

const render = () => {
  const container = document.getElementById("root");

  // Null check to keep TypeScript happy
  if (container === null) {
    throw new Error("Root container is missing in index.html");
  }
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <GlobalStyles
            styles={{
              html: {
                height: "100%",
              },
              body: {
                height: "100%",
                margin: 0,
                overflow: "hidden", // prevent body scroll
              },
              "#root": {
                height: "100%",
                overflow: "hidden", // prevent root scroll
              },
              "*": {
                msOverflowStyle: "none",
                scrollbarWidth: "none",
              },
              "*::-webkit-scrollbar": {
                display: "none",
              },
            }}
          />
          <StyledEngineProvider injectFirst>
            <AuthWrapper>
              <App />
            </AuthWrapper>
          </StyledEngineProvider>
        </ThemeProvider>
      </Provider>
    </StrictMode>,
  );
};

render();
