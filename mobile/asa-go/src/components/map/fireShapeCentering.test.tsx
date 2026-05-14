import { describe, expect, it, vi, beforeEach } from "vitest";
import { centerOnFireShape } from "@/components/map/fireShapeCentering";
import { Map } from "ol";

// Mock the fireZoneExtentsMap
const mockFireZoneExtentsMap = new globalThis.Map([
  [
    "123",
    [
      -1.3280559041253906e7, 6274868.297736709, -1.3139838132862406e7,
      6431584.604443101,
    ],
  ],
  [
    "456",
    [
      -1.3473946106509669e7, 6800425.7877606945, -1.3157325389145028e7,
      7133536.671827988,
    ],
  ],
]);

describe("centerOnFireShape", () => {
  let mockMap: Map;
  let mockAnimate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockAnimate = vi.fn();
    mockMap = {
      getView: vi.fn(() => ({
        animate: mockAnimate,
      })),
    } as unknown as Map;
  });

  const mockFireShape = {
    fire_shape_id: 123,
    mof_fire_zone_name: "Test Fire Zone - Test Area",
    mof_fire_centre_name: "Test Fire Centre",
    area_sqm: 1000000,
  };

  const mockFireShapeWithoutExtent = {
    fire_shape_id: 999,
    mof_fire_zone_name: "Unknown Fire Zone",
    mof_fire_centre_name: "Unknown Fire Centre",
    area_sqm: 500000,
  };

  it("centers map on selected fire shape when fire shape has extent", () => {
    centerOnFireShape(mockMap, mockFireShape, mockFireZoneExtentsMap);

    const expectedExtent = mockFireZoneExtentsMap.get("123")!;
    const expectedCenterX = (expectedExtent[0] + expectedExtent[2]) / 2;
    const expectedCenterY = (expectedExtent[1] + expectedExtent[3]) / 2;

    expect(mockAnimate).toHaveBeenCalledWith({
      center: [expectedCenterX, expectedCenterY],
      duration: 400,
    });
  });

  it("does not animate when selected fire shape has no extent", () => {
    centerOnFireShape(mockMap, mockFireShapeWithoutExtent, mockFireZoneExtentsMap);

    expect(mockAnimate).not.toHaveBeenCalled();
  });

  it("does not animate when selectedFireShape is undefined", () => {
    centerOnFireShape(mockMap, undefined, mockFireZoneExtentsMap);

    expect(mockAnimate).not.toHaveBeenCalled();
  });

  it("does not animate when map is null", () => {
    centerOnFireShape(null, mockFireShape, mockFireZoneExtentsMap);

    expect(mockAnimate).not.toHaveBeenCalled();
  });

  it("calculates correct center coordinates for different fire zone extents", () => {
    const fireShapeWithDifferentExtent = {
      fire_shape_id: 456,
      mof_fire_zone_name: "Different Fire Zone",
      mof_fire_centre_name: "Different Fire Centre",
      area_sqm: 2000000,
    };

    centerOnFireShape(mockMap, fireShapeWithDifferentExtent, mockFireZoneExtentsMap);

    const expectedExtent = mockFireZoneExtentsMap.get("456")!;
    const expectedCenterX = (expectedExtent[0] + expectedExtent[2]) / 2;
    const expectedCenterY = (expectedExtent[1] + expectedExtent[3]) / 2;

    expect(mockAnimate).toHaveBeenCalledWith({
      center: [expectedCenterX, expectedCenterY],
      duration: 400,
    });
  });

  it("converts fire_shape_id to string when looking up extent", () => {
    const getSpy = vi.spyOn(mockFireZoneExtentsMap, "get");

    centerOnFireShape(mockMap, mockFireShape, mockFireZoneExtentsMap);

    expect(getSpy).toHaveBeenCalledWith("123");
  });

  it("preserves zoom level by only setting center coordinates", () => {
    centerOnFireShape(mockMap, mockFireShape, mockFireZoneExtentsMap);

    // Verify that animate was called with only center and duration
    // No zoom parameter should be passed to preserve current zoom level
    expect(mockAnimate).toHaveBeenCalledWith(
      expect.objectContaining({
        center: expect.any(Array),
        duration: 400,
      })
    );

    // Verify no zoom parameter is included
    expect(mockAnimate).toHaveBeenCalledWith(
      expect.not.objectContaining({
        zoom: expect.any(Number),
      })
    );
  });

  it("calculates center coordinates correctly using extent bounds", () => {
    const testExtent = [-1.4e7, 6.5e6, -1.3e7, 7.0e6];
    const testFireZoneExtentsMap = new globalThis.Map([["789", testExtent]]);

    const testFireShape = {
      fire_shape_id: 789,
      mof_fire_zone_name: "Test Zone",
      mof_fire_centre_name: "Test Centre",
      area_sqm: 1500000,
    };

    centerOnFireShape(mockMap, testFireShape, testFireZoneExtentsMap);

    const expectedCenterX = (testExtent[0] + testExtent[2]) / 2;
    const expectedCenterY = (testExtent[1] + testExtent[3]) / 2;

    expect(mockAnimate).toHaveBeenCalledWith({
      center: [expectedCenterX, expectedCenterY],
      duration: 400,
    });

    // Verify the calculation is correct
    expect(expectedCenterX).toBe((-1.4e7 + -1.3e7) / 2);
    expect(expectedCenterY).toBe((6.5e6 + 7.0e6) / 2);
  });
});
