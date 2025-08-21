import { setZoneStatusLayerVisibility } from "./layerVisibility";
import VectorTileLayer from "ol/layer/VectorTile";
import { FireShapeArea } from "@/api/fbaAPI";
import { vi } from "vitest";
import * as featureStylers from "@/featureStylers";

describe("setZoneStatusLayerVisibility", () => {
  it("calls setStyle with a function from fireShapeStyler and that function returns a Style", () => {
    const layer = new VectorTileLayer();
    const fireShapeAreas: FireShapeArea[] = [];
    const advisoryThreshold = 10;
    const visible = true;

    const setStyleSpy = vi.spyOn(layer, "setStyle");
    const fireShapeStylerSpy = vi.spyOn(featureStylers, "fireShapeStyler");

    setZoneStatusLayerVisibility(
      layer,
      fireShapeAreas,
      advisoryThreshold,
      visible
    );

    expect(setStyleSpy).toHaveBeenCalled();
    expect(fireShapeStylerSpy).toHaveBeenCalledWith(
      expect.any(Array),
      advisoryThreshold,
      visible
    );

    const styleFn = setStyleSpy.mock.calls[0][0];
    expect(typeof styleFn).toBe("function");
  });
});
