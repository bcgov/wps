import { FireShape } from "@/api/fbaAPI";
import { isNull, isUndefined } from "lodash";
import { Map, Overlay } from "ol";

export const centerOnFireShape = (
  map: Map | null,
  selectedFireShape: FireShape | undefined,
  fireZoneExtentsMap: globalThis.Map<string, number[]>,
  popup: Overlay
) => {
  if (isNull(map)) {
    return;
  }
  if (selectedFireShape) {
    const zoneExtent = fireZoneExtentsMap.get(
      selectedFireShape.fire_shape_id.toString()
    );
    if (!isUndefined(zoneExtent)) {
      // Calculate center of the extent
      const centerX = (zoneExtent[0] + zoneExtent[2]) / 2;
      const centerY = (zoneExtent[1] + zoneExtent[3]) / 2;

      map.getView().animate({
        center: [centerX, centerY],
        duration: 400,
      });
    }
  }
  popup.setPosition(undefined);
};
