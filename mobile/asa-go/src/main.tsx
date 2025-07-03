import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline } from "@mui/material";
import { ThemeProvider, StyledEngineProvider } from "@mui/material/styles";
import { Provider } from "react-redux";
import { store } from "@/store";
import { theme } from "@/theme.ts";
import App from "@/App.tsx";
import { registerPlugin } from "@capacitor/core";
import { Capacitor } from "@capacitor/core";
import type { EchoPlugin } from "./definitions";

console.log("🔌 JS: Platform:", Capacitor.getPlatform());
console.log("🔌 JS: Is native platform:", Capacitor.isNativePlatform());
console.log("🔌 JS: Registering Echo plugin...");
const Echo = registerPlugin<EchoPlugin>("Echo", {
  web: () => import("./web").then((m) => new m.EchoWeb()),
});
console.log("🔌 JS: Echo plugin registered:", Echo);

// Example usage
const echoValue = async (message: string) => {
  console.log("🔌 JS: Calling echo with message:", message);
  console.log("🔌 JS: Platform at call time:", Capacitor.getPlatform());
  try {
    const result = await Echo.echo({ value: message });
    console.log("🔌 JS: Echo result:", result.value); // Will log the same message back
    return result.value;
  } catch (error) {
    console.error("🔌 JS: Echo failed:", error);
    console.error("🔌 JS: Error details:", JSON.stringify(error, null, 2));
  }
};

// Call it
console.log("🔌 JS: About to call echoValue...");
echoValue("Hello World!");

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
            <App />
          </StyledEngineProvider>
        </ThemeProvider>
      </Provider>
    </StrictMode>
  );
};

render();
