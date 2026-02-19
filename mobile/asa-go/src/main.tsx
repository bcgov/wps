import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline } from "@mui/material";
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
