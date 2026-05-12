import PortraitLandingPage from "@/components/PortraitLandingPage";
import { useIsTablet } from "@/hooks/useIsTablet";
import { useIsXSSmallScreen } from "@/hooks/useIsXSScreen";
import { theme } from "@/theme";
import { ThemeProvider } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/hooks/useIsXSScreen", () => ({ useIsXSSmallScreen: vi.fn() }));
vi.mock("@/hooks/useIsTablet", () => ({ useIsTablet: vi.fn() }));
vi.mock("@/components/LoginActions", () => ({
  default: ({ direction }: { direction?: string }) => (
    <div data-testid="login-actions" data-direction={direction ?? "column"} />
  ),
}));
vi.mock("@/assets/asa-go-transparent.png", () => ({
  default: "mocked-image.png",
}));

const renderComponent = () =>
  render(
    <ThemeProvider theme={theme}>
      <PortraitLandingPage />
    </ThemeProvider>,
  );

describe("PortraitLandingPage", () => {
  beforeEach(() => {
    vi.mocked(useIsXSSmallScreen).mockReturnValue(false);
    vi.mocked(useIsTablet).mockReturnValue(false);
  });

  describe("static content", () => {
    it("renders the ASA Go title", () => {
      renderComponent();

      expect(screen.getByText("ASA Go")).toBeInTheDocument();
    });

    it("renders the app description", () => {
      renderComponent();

      expect(screen.getByTestId("app-description-p1")).toBeInTheDocument();
      expect(screen.getByTestId("app-description-p2")).toBeInTheDocument();
    });

    it("renders the icon", () => {
      renderComponent();

      expect(screen.getByRole("img")).toHaveAttribute("src", "mocked-image.png");
    });

    it("renders LoginActions with column direction", () => {
      renderComponent();

      expect(screen.getByTestId("login-actions")).toHaveAttribute(
        "data-direction",
        "column",
      );
    });
  });

  describe("screen size variants", () => {
    it("renders an h4 title on XS small screens", () => {
      vi.mocked(useIsXSSmallScreen).mockReturnValue(true);
      vi.mocked(useIsTablet).mockReturnValue(false);
      renderComponent();

      expect(
        screen.getByRole("heading", { level: 4, name: "ASA Go" }),
      ).toBeInTheDocument();
    });

    it("renders an h3 title on regular phone screens", () => {
      vi.mocked(useIsXSSmallScreen).mockReturnValue(false);
      vi.mocked(useIsTablet).mockReturnValue(false);
      renderComponent();

      expect(
        screen.getByRole("heading", { level: 3, name: "ASA Go" }),
      ).toBeInTheDocument();
    });

    it("renders an h2 title on tablet screens", () => {
      vi.mocked(useIsXSSmallScreen).mockReturnValue(false);
      vi.mocked(useIsTablet).mockReturnValue(true);
      renderComponent();

      expect(
        screen.getByRole("heading", { level: 2, name: "ASA Go" }),
      ).toBeInTheDocument();
    });
  });
});
