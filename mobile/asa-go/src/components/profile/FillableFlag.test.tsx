import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import FillableFlag from "@/components/profile/FillableFlag";

describe("FillableFlag", () => {
  it("renders an SVG with expected dimensions", () => {
    render(<FillableFlag maskId="test" percent={50} />);

    const svg = screen.getByRole("img");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute("width", "100");
    expect(svg).toHaveAttribute("height", "43");
    expect(svg).toHaveAttribute("viewBox", "0 0 120 43");
  });

  it("generates mask IDs from maskId prop", () => {
    const { container } = render(
      <div>
        <FillableFlag maskId="upper" percent={50} />
        <FillableFlag maskId="mid" percent={75} />
      </div>,
    );

    const masks = container.querySelectorAll("mask");
    expect(masks).toHaveLength(2);
    expect(masks[0]).toHaveAttribute("id", "mask-upper");
    expect(masks[1]).toHaveAttribute("id", "mask-mid");
  });

  it("calculates fill width from percent", () => {
    const cases = [
      { percent: 0, expectedWidth: "0" },
      { percent: 25, expectedWidth: "30" },
      { percent: 50, expectedWidth: "60" },
      { percent: 75, expectedWidth: "90" },
      { percent: 100, expectedWidth: "120" },
    ];

    cases.forEach(({ percent, expectedWidth }) => {
      const { container } = render(
        <FillableFlag maskId={`mask-${percent}`} percent={percent} />,
      );
      const maskRect = container.querySelector("mask rect");
      expect(maskRect).toHaveAttribute("width", expectedWidth);
      expect(maskRect).toHaveAttribute("height", "43");
      expect(maskRect).toHaveAttribute("fill", "white");
    });
  });

  it("applies the mask to the filled path only", () => {
    const { container } = render(<FillableFlag maskId="test-mask" percent={75} />);

    const paths = container.querySelectorAll("path");
    expect(paths).toHaveLength(2);

    const filledPath = paths[0];
    const outlinePath = paths[1];

    expect(filledPath).toHaveAttribute("mask", "url(#mask-test-mask)");
    expect(filledPath).toHaveAttribute("fill", "black");
    expect(outlinePath).not.toHaveAttribute("mask");
  });

  it("does not render percent text", () => {
    const { container } = render(<FillableFlag maskId="test" percent={42} />);
    expect(container.querySelector("text")).not.toBeInTheDocument();
    expect(container.querySelector("filter")).not.toBeInTheDocument();
  });
});
