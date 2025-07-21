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
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the AppHeader with title and HamburgerMenu", () => {
    render(<AppHeader />);

    // Check for title
    expect(screen.getByText("ASA")).toBeInTheDocument();

    // Check for HamburgerMenu with correct props
    const hamburger = screen.getByTestId("hamburger-menu");
    expect(hamburger).toHaveTextContent("drawerTop: 120");
    expect(hamburger).toHaveTextContent("drawerHeight: 680");
  });
});
