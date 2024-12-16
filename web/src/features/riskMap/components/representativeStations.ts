import { GeoJsonStation, DetailedGeoJsonStation } from '@/api/stationAPI'
import Feature, { FeatureLike } from 'ol/Feature'
import VectorLayer from 'ol/layer/Vector'
import { Geometry } from 'ol/geom'
import GeoJSON from 'ol/format/GeoJSON'
import VectorSource from 'ol/source/Vector'
import { Fill, Stroke, Style } from 'ol/style'
import CircleStyle from 'ol/style/Circle'
import { getDistance } from 'ol/sphere'
import RenderFeature from 'ol/render/Feature'
import * as turf from '@turf/turf'

// const getClosestStation = (refPoint: any[], stations: GeoJsonStation[] | DetailedGeoJsonStation[]) => {
//   let minDistance = Infinity
//   let closestStation: GeoJsonStation | DetailedGeoJsonStation | null = null
//   stations.forEach(station => {
//     const targetGeom = station.geometry
//     const distance = getDistance(refPoint.geometry.coordinates, targetGeom.coordinates)
//     if (distance < minDistance) {
//       closestStation = station
//     }
//   })

//   return closestStation
// }

// const getClosestTargets = (
//   firePerimeterGeojson: Feature<Geometry>[],
//   stations: GeoJsonStation[] | DetailedGeoJsonStation[]
// ) => {
//   const closestTargets = new Set()
//   if (!firePerimeterGeojson) return

//   firePerimeterGeojson.forEach(refFeature => {
//     const refGeom = refFeature.getGeometry()
//     if (!refGeom) return

//     if (refGeom.getType() === 'MultiPolygon') {
//       console.log('Got multipolygon')
//       const multiPolygon = turf.multiPolygon(refGeom.getCoordinates())
//       // Compute the centroid (center of mass)
//       const centroid = turf.centerOfMass(multiPolygon)
//       console.log('centroid point:', centroid)
//       const closestStation = getClosestStation(centroid, stations)
//       console.log('closest', closestStation)
//       if (typeof closestStation == 'object') {
//         console.log(closestStation)
//       }
//     }

//     if (refGeom.getType() === 'Polygon') {
//       const geoJsonFormat = new GeoJSON()
//       const geoJsonPolygon = geoJsonFormat.writeFeatureObject(refFeature)
//       const center = turf.center(geoJsonPolygon)
//       console.log('center point: ', center)
//       const closestStation = getClosestStation(center, stations)
//       console.log('closest', closestStation)
//       if (typeof closestStation == 'object') {
//         console.log(closestStation)
//       }
//     }
//   })

//   return closestTargets
// }

export const getStations = (stations: GeoJsonStation[] | DetailedGeoJsonStation[]) => {
  const stationLayer = new VectorLayer({
    source: new VectorSource({
      features: new GeoJSON().readFeatures(
        { type: 'FeatureCollection', features: stations },
        {
          featureProjection: 'EPSG:3857'
        }
      )
    }),
    style: (_: Feature<Geometry> | RenderFeature) => {
      return new Style({
        image: new CircleStyle({
          radius: 3,
          fill: new Fill({ color: 'black' })
        })
      })
    },
    zIndex: 101
  })
  return stationLayer
}
