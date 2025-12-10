import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { AppHeader } from "@/components/AppHeader";

// Mock HamburgerMenu to inspect props
vi.mock("@/components/HamburgerMenu", () => ({
  HamburgerMenu: ({
    drawerTop,
    drawerHeight,
    testId,
  }: {
    drawerTop: number;
    drawerHeight: number;
    testId?: string;
  }) => (
    <div data-testid={testId}>
      drawerTop: {drawerTop}, drawerHeight: {drawerHeight}
    </div>
  ),
}));

// Mock useMediaQuery
vi.mock("@mui/material", async () => {
  const actual = await vi.importActual("@mui/material");
  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

import { useMediaQuery } from "@mui/material";

describe("AppHeader", () => {
  beforeEach(() => {
    // Mock getBoundingClientRect
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
      bottom: 120,
      height: 100,
      top: 20,
      left: 0,
      right: 0,
      width: 0,
      x: 0,
      y: 0,
      toJSON: () => {},
    });

    // Mock window.innerHeight
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 800,
    });

    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the AppHeader with title and HamburgerMenu in portrait mode", () => {
    // Mock: portrait orientation, small device
    vi.mocked(useMediaQuery).mockImplementation((query) => {
      if (query === "(orientation: landscape)") return false;
      if (query === "(min-width: 768px)") return false;
      return false;
    });
    render(<AppHeader />);

    // Check for title
    expect(screen.getByText("ASA")).toBeInTheDocument();

    // Check for HamburgerMenu with correct props
    const hamburger = screen.getByTestId("hamburger-menu");
    expect(hamburger).toHaveTextContent("drawerTop: 120");
    expect(hamburger).toHaveTextContent("drawerHeight: 680");
  });

  it("hides the AppHeader on small devices in landscape mode", () => {
    // Mock: landscape orientation, small device
    vi.mocked(useMediaQuery).mockImplementation((query) => {
      if (query === "(orientation: landscape)") return true;
      if (query === "(min-width: 768px)") return false;
      return false;
    });
    const { container } = render(<AppHeader />);

    // Component should return null, so container should be empty
    expect(container.firstChild).toBeNull();

    // Title should not be in the document
    expect(screen.queryByText("ASA")).not.toBeInTheDocument();

    // HamburgerMenu should not be in the document
    expect(screen.queryByTestId("hamburger-menu")).not.toBeInTheDocument();
  });

  it("shows the AppHeader on large devices (iPads) in landscape mode", () => {
    // Mock: landscape orientation, large device
    vi.mocked(useMediaQuery).mockImplementation((query) => {
      if (query === "(orientation: landscape)") return true;
      if (query === "(min-width: 768px)") return true;
      return false;
    });
    render(<AppHeader />);

    // Should show the header even in landscape on large devices
    expect(screen.getByText("ASA")).toBeInTheDocument();
    expect(screen.getByTestId("hamburger-menu")).toBeInTheDocument();
  });

  it("shows the AppHeader when orientation changes from landscape to portrait on small device", () => {
    // Start in landscape on small device
    vi.mocked(useMediaQuery).mockImplementation((query) => {
      if (query === "(orientation: landscape)") return true;
      if (query === "(min-width: 768px)") return false;
      return false;
    });
    const { rerender } = render(<AppHeader />);
    expect(screen.queryByText("ASA")).not.toBeInTheDocument();

    // Change to portrait on small device
    vi.mocked(useMediaQuery).mockImplementation((query) => {
      if (query === "(orientation: landscape)") return false;
      if (query === "(min-width: 768px)") return false;
      return false;
    });
    rerender(<AppHeader />);

    // Should now show the header
    expect(screen.getByText("ASA")).toBeInTheDocument();
    expect(screen.getByTestId("hamburger-menu")).toBeInTheDocument();
  });
});
