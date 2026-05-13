import PublicLoginButton from "@/components/PublicLoginButton";
import { continueAsGuest } from "@/slices/authenticationSlice";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { useDispatch } from "react-redux";
import { Mock, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-redux", async () => {
  const actual = await vi.importActual("react-redux");
  return {
    ...actual,
    useDispatch: vi.fn(),
  };
});

vi.mock("@/slices/authenticationSlice", () => ({
  continueAsGuest: vi.fn(() => ({ type: "CONTINUE_AS_GUEST" })),
}));

describe("PublicLoginButton", () => {
  const mockDispatch = vi.fn();
  const theme = createTheme();

  beforeEach(() => {
    (useDispatch as unknown as Mock).mockReturnValue(mockDispatch);
    mockDispatch.mockClear();
  });

  const renderComponent = () =>
    render(
      <ThemeProvider theme={theme}>
        <PublicLoginButton />
      </ThemeProvider>,
    );

  it("renders the continue as guest button", () => {
    renderComponent();

    expect(
      screen.getByRole("button", { name: /continue as guest/i }),
    ).toBeInTheDocument();
  });

  it("dispatches continueAsGuest on click", () => {
    renderComponent();

    fireEvent.click(screen.getByRole("button", { name: /continue as guest/i }));

    expect(mockDispatch).toHaveBeenCalledWith(continueAsGuest());
  });
});
