import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FillableFlag from "@/components/profile/FillableFlag";

describe("FillableFlag", () => {
  // Test basic rendering
  it("should render an SVG element", () => {
    render(<FillableFlag maskId="test" percent={50} testId="test-flag" />);

    const svg = screen.getByRole("img");
    expect(svg).toBeInTheDocument();
    expect(svg.tagName).toBe("svg");
  });

  // Test SVG attributes
  it("should have correct SVG dimensions and viewBox", () => {
    render(<FillableFlag maskId="test" percent={50} />);

    const svg = screen.getByRole("img");
    expect(svg).toHaveAttribute("width", "120");
    expect(svg).toHaveAttribute("height", "43");
    expect(svg).toHaveAttribute("viewBox", "0 0 120 43");
  });

  // Test percent text rendering
  it("should display the correct percent value", () => {
    render(<FillableFlag maskId="test" percent={75} testId="test-flag" />);

    const percentText = screen.getByTestId("test-flag");
    expect(percentText).toBeInTheDocument();
    expect(percentText).toHaveTextContent("75%");
  });

  // Test different percent values
  it.each([
    [0, "0%"],
    [25, "25%"],
    [50, "50%"],
    [75, "75%"],
    [100, "100%"],
  ])("should display %i percent as '%s'", (percent, expectedText) => {
    render(<FillableFlag maskId="test" percent={percent} testId="test-flag" />);

    const percentText = screen.getByTestId("test-flag");
    expect(percentText).toHaveTextContent(expectedText);
  });

  // Test mask ID generation
  it("should generate unique mask IDs", () => {
    const { container } = render(
      <div>
        <FillableFlag maskId="upper" percent={50} />
        <FillableFlag maskId="mid" percent={75} />
      </div>
    );

    // Check that mask IDs are unique
    const masks = container.querySelectorAll("mask");
    expect(masks).toHaveLength(2);
    expect(masks[0]).toHaveAttribute("id", "mask-upper");
    expect(masks[1]).toHaveAttribute("id", "mask-mid");
  });

  // Test filter ID generation
  it("should generate unique filter IDs", () => {
    const { container } = render(
      <div>
        <FillableFlag maskId="upper" percent={50} />
        <FillableFlag maskId="mid" percent={75} />
      </div>
    );

    const filters = container.querySelectorAll("filter");
    expect(filters).toHaveLength(2);
    expect(filters[0]).toHaveAttribute("id", "shadow-upper");
    expect(filters[1]).toHaveAttribute("id", "shadow-mid");
  });

  // Test fill width calculation
  it("should calculate correct fill width for different percentages", () => {
    const testCases = [
      { percent: 0, expectedWidth: "0" },
      { percent: 25, expectedWidth: "30" }, // 25% of 120
      { percent: 50, expectedWidth: "60" }, // 50% of 120
      { percent: 75, expectedWidth: "90" }, // 75% of 120
      { percent: 100, expectedWidth: "120" }, // 100% of 120
    ];

    testCases.forEach(({ percent, expectedWidth }) => {
      const { container } = render(
        <FillableFlag maskId="test" percent={percent} />
      );

      const maskRect = container.querySelector("mask rect");
      expect(maskRect).toHaveAttribute("width", expectedWidth);
    });
  });

  // Test that fill width directly matches percent calculation
  it("should have fill width that matches percent calculation", () => {
    const percentValues = [0, 10, 33, 45, 67, 89, 100];
    const svgWidth = 120;

    percentValues.forEach((percent) => {
      const { container } = render(
        <FillableFlag maskId={`test-${percent}`} percent={percent} />
      );

      const maskRect = container.querySelector("mask rect");
      const expectedWidth = (percent / 100) * svgWidth;

      expect(maskRect).toHaveAttribute("width", expectedWidth.toString());

      // Verify the calculation is correct
      expect(Number(maskRect?.getAttribute("width"))).toBe(expectedWidth);
    });
  });

  // Test visual fill representation matches percent
  it("should have mask rectangle that represents the correct fill percentage", () => {
    const testScenarios = [
      { percent: 0 }, // 0% should show no fill
      { percent: 50 }, // 50% should fill half the flag
      { percent: 100 }, // 100% should fill the entire flag
    ];

    testScenarios.forEach(({ percent }) => {
      const { container } = render(
        <FillableFlag maskId={`scenario-${percent}`} percent={percent} />
      );

      const maskRect = container.querySelector("mask rect");

      // Verify mask rectangle starts at origin
      expect(maskRect).toHaveAttribute("x", "0");
      expect(maskRect).toHaveAttribute("y", "0");

      // Verify height covers full flag height
      expect(maskRect).toHaveAttribute("height", "43");

      // Verify width matches percentage of total width
      const expectedFillWidth = (percent / 100) * 120;
      expect(maskRect).toHaveAttribute("width", expectedFillWidth.toString());

      // Verify fill color is white (shows through mask)
      expect(maskRect).toHaveAttribute("fill", "white");
    });
  });

  // Test that filled path uses the correct mask
  it("should apply mask to the filled path element", () => {
    const { container } = render(
      <FillableFlag maskId="test-mask" percent={75} />
    );

    const paths = container.querySelectorAll("path");
    const filledPath = paths[0]; // First path is the filled one
    const outlinePath = paths[1]; // Second path is outline only

    // Filled path should have mask applied
    expect(filledPath).toHaveAttribute("mask", "url(#mask-test-mask)");
    expect(filledPath).toHaveAttribute("fill", "black");

    // Outline path should not have mask
    expect(outlinePath).not.toHaveAttribute("mask");
    expect(outlinePath).not.toHaveAttribute("fill");
  });

  // Test SVG structure
  it("should have the correct SVG structure", () => {
    const { container } = render(
      <FillableFlag maskId="test" percent={50} testId="test-flag" />
    );

    // Should have defs section with mask and filter
    const defs = container.querySelector("defs");
    expect(defs).toBeInTheDocument();

    // Should have mask with rect
    const mask = container.querySelector("mask");
    const maskRect = container.querySelector("mask rect");
    expect(mask).toBeInTheDocument();
    expect(maskRect).toBeInTheDocument();

    // Should have filter with drop shadows
    const filter = container.querySelector("filter");
    const dropShadows = container.querySelectorAll("feDropShadow");
    expect(filter).toBeInTheDocument();
    expect(dropShadows).toHaveLength(4); // Four drop shadows for text outline

    // Should have two path elements (filled and outline)
    const paths = container.querySelectorAll("path");
    expect(paths).toHaveLength(2);

    // Should have text element
    const text = container.querySelector("text");
    expect(text).toBeInTheDocument();
  });

  // Test text positioning
  it("should position text in the center of the SVG", () => {
    const { container } = render(
      <FillableFlag maskId="test" percent={50} testId="test-flag" />
    );

    const text = container.querySelector("text");
    expect(text).toHaveAttribute("x", "60"); // Center of 120px width
    expect(text).toHaveAttribute("y", "21.5"); // Center of 43px height
    expect(text).toHaveAttribute("text-anchor", "middle");
    expect(text).toHaveAttribute("dominant-baseline", "central");
  });

  // Test text styling
  it("should have correct text styling", () => {
    const { container } = render(
      <FillableFlag maskId="test" percent={50} testId="test-flag" />
    );

    const text = container.querySelector("text");
    expect(text).toHaveAttribute("font-size", "16");
    expect(text).toHaveAttribute("font-weight", "bold");
    expect(text).toHaveAttribute("fill", "black");
    expect(text).toHaveAttribute("filter", "url(#shadow-test)");
  });

  // Test drop shadow configuration
  it("should have correct drop shadow configuration", () => {
    const { container } = render(<FillableFlag maskId="test" percent={50} />);

    const dropShadows = container.querySelectorAll("feDropShadow");
    expect(dropShadows).toHaveLength(4);

    // Test each drop shadow matches CSS text-shadow equivalent
    const expectedShadows = [
      { dx: "-2", dy: "2" }, // -2px 2px
      { dx: "2", dy: "2" }, // 2px 2px
      { dx: "2", dy: "-2" }, // 2px -2px
      { dx: "-2", dy: "-2" }, // -2px -2px
    ];

    dropShadows.forEach((shadow, index) => {
      const expected = expectedShadows[index];
      expect(shadow).toHaveAttribute("dx", expected.dx);
      expect(shadow).toHaveAttribute("dy", expected.dy);
      expect(shadow).toHaveAttribute("stdDeviation", "4"); // 4px blur
      expect(shadow).toHaveAttribute("flood-color", "white");
      expect(shadow).toHaveAttribute("flood-opacity", "1");
    });
  });

  // Test path elements
  it("should have correct path configuration", () => {
    const { container } = render(<FillableFlag maskId="test" percent={50} />);

    const paths = container.querySelectorAll("path");
    const expectedPath =
      "M10.7443 41.822L0.558603 21.375L10.7443 0.928009L119.5 0.928009L119.5 41.822L10.7443 41.822Z";

    // First path (filled with mask)
    expect(paths[0]).toHaveAttribute("d", expectedPath);
    expect(paths[0]).toHaveAttribute("stroke", "black");
    expect(paths[0]).toHaveAttribute("fill", "black");
    expect(paths[0]).toHaveAttribute("mask", "url(#mask-test)");

    // Second path (outline only)
    expect(paths[1]).toHaveAttribute("d", expectedPath);
    expect(paths[1]).toHaveAttribute("stroke", "black");
    expect(paths[1]).not.toHaveAttribute("fill");
  });

  // Test edge cases
  it("should handle edge case percentages", () => {
    const edgeCases = [
      { percent: -5, expectedText: "-5%" }, // Negative
      { percent: 0, expectedText: "0%" }, // Zero
      { percent: 105, expectedText: "105%" }, // Over 100
    ];

    edgeCases.forEach(({ percent, expectedText }, idx) => {
      render(
        <FillableFlag
          maskId={`test-${idx}`}
          percent={percent}
          testId={`test-flag-${idx}`}
        />
      );

      const percentText = screen.getByTestId(`test-flag-${idx}`);
      expect(percentText).toHaveTextContent(expectedText);
    });
  });
});
