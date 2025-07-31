import { render, screen, fireEvent } from "@testing-library/react";
import { Mock, vi } from "vitest";
import LoginButton from "@/components/LoginButton";
import { useDispatch } from "react-redux";
import { authenticate } from "@/slices/authenticationSlice";
import { setAxiosRequestInterceptors } from "@/utils/axiosInterceptor";
import { ThemeProvider, createTheme } from "@mui/material/styles";

// Mocks
vi.mock("react-redux", async () => {
  const actual = await vi.importActual("react-redux");
  return {
    ...actual,
    useDispatch: vi.fn(),
  };
});

vi.mock("@/slices/authenticationSlice", () => ({
  authenticate: vi.fn(() => ({ type: "AUTHENTICATE" })),
}));

vi.mock("@/utils/axiosInterceptor", () => ({
  setAxiosRequestInterceptors: vi.fn(() => ({ type: "SET_INTERCEPTORS" })),
}));

describe("LoginButton", () => {
  const mockDispatch = vi.fn();
  const theme = createTheme();

  beforeEach(() => {
    (useDispatch as unknown as Mock).mockReturnValue(mockDispatch);
    mockDispatch.mockClear();
  });

  it("renders the button with the correct label", () => {
    render(
      <ThemeProvider theme={theme}>
        <LoginButton label="Sign In" />
      </ThemeProvider>
    );

    expect(screen.getByText("Sign In")).toBeInTheDocument();
  });

  it("dispatches authenticate and setAxiosRequestInterceptors on click", () => {
    render(
      <ThemeProvider theme={theme}>
        <LoginButton label="Sign In" />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(mockDispatch).toHaveBeenCalledWith(authenticate());
    expect(mockDispatch).toHaveBeenCalledWith(setAxiosRequestInterceptors());
  });
});
