import { render } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import UserLocationIndicator from "./LocationIndicator";
import { Map } from "ol";
import { Position } from "@capacitor/geolocation";

// Mock OpenLayers
vi.mock("ol", () => ({
  Map: vi.fn(),
  Overlay: vi.fn().mockImplementation(() => ({
    setPosition: vi.fn(),
    getElement: vi.fn(),
  })),
}));

vi.mock("ol/proj", () => ({
  fromLonLat: vi.fn(([lon, lat]) => [lon * 111319.49, lat * 110540.1]),
}));

describe("UserLocationIndicator", () => {
  let mockMap: Map;
  let addOverlay: ReturnType<typeof vi.fn>;
  let removeOverlay: ReturnType<typeof vi.fn>;

  const mockPosition: Position = {
    coords: {
      latitude: 49.2827,
      longitude: -123.1207,
      accuracy: 10,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
    timestamp: Date.now(),
  };

  beforeEach(() => {
    addOverlay = vi.fn();
    removeOverlay = vi.fn();

    mockMap = {
      addOverlay,
      removeOverlay,
    } as unknown as Map;

    vi.clearAllMocks();
  });

  it("renders the blue dot indicator", () => {
    const { getByTestId } = render(
      <UserLocationIndicator map={mockMap} position={mockPosition} />
    );

    const indicator = getByTestId("user-location-indicator");
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveStyle({
      width: "20px",
      height: "20px",
      borderRadius: "50%",
      backgroundColor: "rgba(51, 153, 204, 0.8)",
    });
  });

  it("adds overlay to map when map and position are provided", () => {
    render(<UserLocationIndicator map={mockMap} position={mockPosition} />);

    expect(addOverlay).toHaveBeenCalledTimes(1);
  });

  it("does not add overlay when map is null", () => {
    render(<UserLocationIndicator map={null} position={mockPosition} />);

    expect(addOverlay).not.toHaveBeenCalled();
  });

  it("removes overlay on cleanup", () => {
    const { unmount } = render(
      <UserLocationIndicator map={mockMap} position={mockPosition} />
    );

    unmount();

    expect(removeOverlay).toHaveBeenCalledTimes(1);
  });

  it("handles null position gracefully", () => {
    const { getByTestId } = render(
      <UserLocationIndicator map={mockMap} position={null} />
    );

    const indicator = getByTestId("user-location-indicator");
    expect(indicator).toBeInTheDocument();
    expect(addOverlay).toHaveBeenCalledTimes(1);
  });

  it("renders with correct styling", () => {
    const { getByTestId } = render(
      <UserLocationIndicator map={mockMap} position={mockPosition} />
    );

    const indicator = getByTestId("user-location-indicator");
    expect(indicator).toHaveStyle({
      border: "3px solid white",
      boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
      pointerEvents: "none",
      zIndex: "1000",
    });
  });
});
