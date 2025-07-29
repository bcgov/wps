import { authenticate } from "@/slices/authenticationSlice";
import { createTestStore } from "@/testUtils";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi } from "vitest";
import LoginButton from "./LoginButton";

// Mock authenticate action
vi.mock("@/slices/authenticationSlice", () => ({
  authenticate: vi.fn(() => ({ type: "AUTHENTICATE" })),
  default: vi.fn(() => null),
}));

const theme = createTheme();

describe("LoginButton", () => {
  it("renders with the correct label", () => {
    const store = createTestStore({});
    render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <LoginButton label="Sign In" />
        </ThemeProvider>
      </Provider>
    );

    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("dispatches authenticate action on click", () => {
    const store = createTestStore({});
    store.dispatch = vi.fn();

    render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <LoginButton label="Login" />
        </ThemeProvider>
      </Provider>
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(store.dispatch).toHaveBeenCalledTimes(1);
    expect(authenticate).toHaveBeenCalled();
  });
});
