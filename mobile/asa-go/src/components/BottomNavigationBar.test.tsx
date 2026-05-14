import { useIsTablet } from "@/hooks/useIsTablet";
import { fireEvent, render, screen } from "@testing-library/react";
import BottomNavigationBar from "@/components/BottomNavigationBar";
import { NavPanel } from "@/utils/constants";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/hooks/useIsTablet", () => ({
  useIsTablet: vi.fn(),
}));

describe("BottomNavigationBar", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(useIsTablet).mockReturnValue(false);
  });

  it("renders all navigation actions", () => {
    render(<BottomNavigationBar tab={NavPanel.MAP} setTab={vi.fn()} />);

    expect(screen.getByRole("button", { name: NavPanel.MAP })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: NavPanel.PROFILE }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: NavPanel.ADVISORY }),
    ).toBeInTheDocument();
  });

  it("applies selected class to the active tab", () => {
    const { rerender } = render(
      <BottomNavigationBar tab={NavPanel.MAP} setTab={vi.fn()} />,
    );

    expect(screen.getByRole("button", { name: NavPanel.MAP })).toHaveClass(
      "Mui-selected",
    );
    expect(screen.getByRole("button", { name: NavPanel.PROFILE })).not.toHaveClass(
      "Mui-selected",
    );

    rerender(<BottomNavigationBar tab={NavPanel.PROFILE} setTab={vi.fn()} />);

    expect(screen.getByRole("button", { name: NavPanel.PROFILE })).toHaveClass(
      "Mui-selected",
    );
    expect(screen.getByRole("button", { name: NavPanel.MAP })).not.toHaveClass(
      "Mui-selected",
    );
  });

  it("calls setTab with the selected tab when clicked", () => {
    const setTab = vi.fn();

    render(<BottomNavigationBar tab={NavPanel.MAP} setTab={setTab} />);

    fireEvent.click(screen.getByRole("button", { name: NavPanel.PROFILE }));
    expect(setTab).toHaveBeenCalledWith(NavPanel.PROFILE);

    fireEvent.click(screen.getByRole("button", { name: NavPanel.ADVISORY }));
    expect(setTab).toHaveBeenCalledWith(NavPanel.ADVISORY);
  });

  it("uses the tablet icon size when the device is tablet-sized", () => {
    vi.mocked(useIsTablet).mockReturnValue(true);

    render(<BottomNavigationBar tab={NavPanel.MAP} setTab={vi.fn()} />);

    expect(screen.getByTestId("MapIcon")).toHaveStyle({ fontSize: "40px" });
  });
});
