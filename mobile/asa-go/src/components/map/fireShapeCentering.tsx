import { isNull, isUndefined } from 'lodash'
import type { Map as OlMap } from 'ol'
import type { FireShape } from '@/api/fbaAPI'

export const centerOnFireShape = (
  map: OlMap | null,
  selectedFireShape: FireShape | undefined,
  fireZoneExtentsMap: globalThis.Map<string, number[]>
) => {
  if (isNull(map)) {
    return
  }
  if (selectedFireShape) {
    const zoneExtent = fireZoneExtentsMap.get(selectedFireShape.fire_shape_id.toString())
    if (!isUndefined(zoneExtent)) {
      // Calculate center of the extent
      const centerX = (zoneExtent[0] + zoneExtent[2]) / 2
      const centerY = (zoneExtent[1] + zoneExtent[3]) / 2

      map.getView().animate({
        center: [centerX, centerY],
        duration: 400
      })
    }
  }
}
