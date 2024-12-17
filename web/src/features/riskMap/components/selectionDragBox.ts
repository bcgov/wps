import { getWidth } from 'ol/extent'
import { DragBox } from 'ol/interaction'
import VectorSource from 'ol/source/Vector'
import { Collection, Feature, Map } from 'ol'
import Geometry from 'ol/geom/Geometry'

export const collectFeaturesWithin = (
  dragBox: DragBox,
  map: Map,
  firePerimeterSource: VectorSource<Feature<Geometry>>,
  selectedFeatures: Collection<Feature<Geometry>>
) => {
  const boxExtent = dragBox.getGeometry().getExtent()

  // if the extent crosses the antimeridian process each world separately
  const worldExtent = map.getView().getProjection().getExtent()
  const worldWidth = getWidth(worldExtent)
  const startWorld = Math.floor((boxExtent[0] - worldExtent[0]) / worldWidth)
  const endWorld = Math.floor((boxExtent[2] - worldExtent[0]) / worldWidth)

  for (let world = startWorld; world <= endWorld; ++world) {
    const left = Math.max(boxExtent[0] - world * worldWidth, worldExtent[0])
    const right = Math.min(boxExtent[2] - world * worldWidth, worldExtent[2])
    const extent = [left, boxExtent[1], right, boxExtent[3]]

    const boxFeatures = firePerimeterSource
      .getFeaturesInExtent(extent)
      .filter(
        feature => !selectedFeatures.getArray().includes(feature) && feature.getGeometry()?.intersectsExtent(extent)
      )

    // features that intersect the box geometry are added to the
    // collection of selected features

    // if the view is not obliquely rotated the box geometry and
    // its extent are equalivalent so intersecting features can
    // be added directly to the collection
    const rotation = map.getView().getRotation()
    const oblique = rotation % (Math.PI / 2) !== 0

    // when the view is obliquely rotated the box extent will
    // exceed its geometry so both the box and the candidate
    // feature geometries are rotated around a common anchor
    // to confirm that, with the box geometry aligned with its
    // extent, the geometries intersect
    if (oblique) {
      const anchor = [0, 0]
      const geometry = dragBox.getGeometry().clone()
      geometry.translate(-world * worldWidth, 0)
      geometry.rotate(-rotation, anchor)
      const extent = geometry.getExtent()
      boxFeatures.forEach(function (feature) {
        const geometry = feature.getGeometry().clone()
        geometry.rotate(-rotation, anchor)
        if (geometry.intersectsExtent(extent)) {
          selectedFeatures.push(feature)
        }
      })
    } else {
      selectedFeatures.extend(boxFeatures)
    }
    return [...selectedFeatures.getArray()]
  }
}
