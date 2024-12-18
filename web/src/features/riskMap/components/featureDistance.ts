import { Feature } from 'ol'
import { toLonLat } from 'ol/proj'
import { Coordinate } from 'ol/coordinate'
import { bearing, distance, point } from '@turf/turf'

export const closestFeatureStats = (features: Feature[], selectedPointCoords: Coordinate) => {
  const lonLatCoords = toLonLat(selectedPointCoords)

  let closestDistance = Infinity
  let closestFeature = null
  let closestBearing = 0

  features.forEach((layerFeature: Feature) => {
    const geometry = layerFeature.getGeometry()
    if (geometry) {
      const closestPoint = geometry.getClosestPoint(selectedPointCoords)
      const closestPointLonLat = toLonLat(closestPoint)

      const turfPointA = point(lonLatCoords)
      const turfPointB = point(closestPointLonLat)

      const dist = distance(turfPointA, turfPointB, { units: 'kilometers' })
      const bearingAngle = bearing(turfPointA, turfPointB)

      if (dist < closestDistance) {
        closestDistance = dist
        closestFeature = layerFeature
        closestBearing = bearingAngle
      }
    }
  })

  return {
    closestDistance,
    closestFeature,
    closestBearing
  }
}
