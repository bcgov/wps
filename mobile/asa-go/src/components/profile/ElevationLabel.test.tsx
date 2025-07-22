import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ElevationLabel from "@/components/profile/ElevationLabel";

describe("ElevationLabel", () => {
  it("should render the label text", () => {
    render(<ElevationLabel label="Upper Slope" />);

    const typography = screen.getByText("Upper Slope");
    expect(typography).toBeInTheDocument();
  });

  it("should render with bold font weight", () => {
    render(<ElevationLabel label="Test Label" />);

    const typography = screen.getByText("Test Label");
    expect(typography).toBeInTheDocument();
    // Check for the MUI class that applies bold font weight
    expect(typography).toHaveClass("MuiTypography-root");
  });

  it("should render different label values", () => {
    const { rerender } = render(<ElevationLabel label="Valley" />);

    expect(screen.getByText("Valley")).toBeInTheDocument();
    expect(screen.getByText("Valley")).toHaveClass("MuiTypography-root");

    rerender(<ElevationLabel label="Mid Slope" />);
    expect(screen.getByText("Mid Slope")).toBeInTheDocument();

    rerender(<ElevationLabel label="Upper Slope" />);
    expect(screen.getByText("Upper Slope")).toBeInTheDocument();
  });

  it("should be wrapped in a Grid component", () => {
    const { container } = render(<ElevationLabel label="Test Label" />);

    const gridElement = container.firstChild;
    expect(gridElement).toHaveClass("MuiGrid2-root");
  });

  it("should handle empty string label", () => {
    render(<ElevationLabel label="" />);

    const typography = screen.getByRole("paragraph");
    expect(typography).toBeInTheDocument();
    expect(typography).toHaveTextContent("");
  });

  it("should handle special characters in label", () => {
    const specialLabel = "Test & Label <> 123";
    render(<ElevationLabel label={specialLabel} />);

    const typography = screen.getByText(specialLabel);
    expect(typography).toBeInTheDocument();
  });
});
