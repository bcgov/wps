import React from "react";
import { render, screen } from "@testing-library/react";
import FuelDistribution from "./FuelDistribution";
import * as colorModule from "@/components/profile/color";
import { vi } from "vitest";

// Mock getColorByFuelTypeCode
vi.mock("@/components/profile/color", () => ({
  getColorByFuelTypeCode: vi.fn(),
}));

describe("FuelDistribution", () => {
  const mockColor = "#123456";
  beforeEach(() => {
    (colorModule.getColorByFuelTypeCode as jest.Mock).mockReturnValue(
      mockColor
    );
  });

  it("renders the fuel distribution box with correct width and background color", () => {
    render(<FuelDistribution code="ABC" percent={42} />);
    const box = screen.getByTestId("fuel-distribution-box");
    expect(box).toBeInTheDocument();
    expect(box).toHaveStyle({
      width: "42%",
      background: mockColor,
      height: "75%",
    });
    expect(colorModule.getColorByFuelTypeCode).toHaveBeenCalledWith("ABC");
  });
});
