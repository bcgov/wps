import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CriticalHours from "@/components/profile/CriticalHours";

// Mock the formatCriticalHoursTimeText utility
vi.mock("@/utils/criticalHoursStartEndTime", () => ({
  formatCriticalHoursTimeText: vi.fn((start: number, end: number) => [
    `${String(start).padStart(2, "0")}:00`,
    `${String(end).padStart(2, "0")}:00`,
  ]),
}));

describe("CriticalHours", () => {
  it("should render formatted critical hours when both start and end are provided", () => {
    render(<CriticalHours start={8} end={18} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("08:00 - 18:00");
  });

  it("should render dash when start is undefined", () => {
    render(<CriticalHours start={undefined} end={18} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("-");
  });

  it("should render dash when end is undefined", () => {
    render(<CriticalHours start={8} end={undefined} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("-");
  });

  it("should render dash when both start and end are undefined", () => {
    render(<CriticalHours start={undefined} end={undefined} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("-");
  });

  it("should render dash when start is null", () => {
    render(<CriticalHours start={null as unknown as number} end={18} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("-");
  });

  it("should render dash when end is null", () => {
    render(<CriticalHours start={8} end={null as unknown as number} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("-");
  });

  it("should handle edge case hours", () => {
    render(<CriticalHours start={0} end={23} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent("00:00 - 23:00");
  });

  it("should have correct Typography styling", () => {
    render(<CriticalHours start={10} end={15} />);

    const element = screen.getByTestId("critical-hours");
    expect(element).toHaveStyle({ fontSize: "0.75rem" });
  });
});
