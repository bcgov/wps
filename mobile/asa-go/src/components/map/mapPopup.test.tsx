import { FireShape } from "@/api/fbaAPI";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import MapPopup from "./MapPopup";

const mockFireShape: FireShape = {
  mof_fire_zone_name: "Test Fire Zone",
  fire_shape_id: 1,
  mof_fire_centre_name: "Test Fire Centre",
};

const renderWithTheme = (ui: React.ReactElement) => {
  const theme = createTheme();
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
};

describe("MapPopup", () => {
  it("renders with fire zone name", () => {
    renderWithTheme(
      <MapPopup
        selectedFireShape={mockFireShape}
        onClose={vi.fn()}
        onSelectProfile={vi.fn()}
        onSelectReport={vi.fn()}
        onSelectZoom={vi.fn()}
      />
    );

    expect(screen.getByText("Test Fire Zone")).toBeInTheDocument();
  });

  it("does not crash when selectedFireShape is undefined", () => {
    renderWithTheme(
      <MapPopup
        selectedFireShape={undefined}
        onClose={vi.fn()}
        onSelectProfile={vi.fn()}
        onSelectReport={vi.fn()}
        onSelectZoom={vi.fn()}
      />
    );

    expect(screen.queryByText("Test Fire Zone")).not.toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    const { queryByTestId } = renderWithTheme(
      <MapPopup
        selectedFireShape={mockFireShape}
        onClose={onClose}
        onSelectProfile={vi.fn()}
        onSelectReport={vi.fn()}
        onSelectZoom={vi.fn()}
      />
    );
    const closeButton = queryByTestId("map-popup-close-button");
    expect(closeButton).toBeInTheDocument();
    fireEvent.click(closeButton!);
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onSelectReport when 'View Report' is clicked", () => {
    const onSelectReport = vi.fn();
    renderWithTheme(
      <MapPopup
        selectedFireShape={mockFireShape}
        onClose={vi.fn()}
        onSelectProfile={vi.fn()}
        onSelectReport={onSelectReport}
        onSelectZoom={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("View Report"));
    expect(onSelectReport).toHaveBeenCalled();
  });

  it("calls onSelectProfile when 'View Profile' is clicked", () => {
    const onSelectProfile = vi.fn();
    renderWithTheme(
      <MapPopup
        selectedFireShape={mockFireShape}
        onClose={vi.fn()}
        onSelectProfile={onSelectProfile}
        onSelectReport={vi.fn()}
        onSelectZoom={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("View Profile"));
    expect(onSelectProfile).toHaveBeenCalled();
  });

  it("calls onSelectZoom when 'Zoom to fire zone' is clicked", () => {
    const onSelectZoom = vi.fn();
    renderWithTheme(
      <MapPopup
        selectedFireShape={mockFireShape}
        onClose={vi.fn()}
        onSelectProfile={vi.fn()}
        onSelectReport={vi.fn()}
        onSelectZoom={onSelectZoom}
      />
    );

    fireEvent.click(screen.getByText("Zoom to fire zone"));
    expect(onSelectZoom).toHaveBeenCalled();
  });
});
