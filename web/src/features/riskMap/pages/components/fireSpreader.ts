import { bbox, polygon } from '@turf/turf'
import GeoJSON from 'ol/format/GeoJSON'
import {
  Point,
  MultiPoint,
  LineString,
  MultiLineString,
  Polygon,
  MultiPolygon,
  Feature,
  Geometry,
  GeoJsonProperties
} from 'geojson'
import { fromLonLat, toLonLat } from 'ol/proj'

import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Fill, Stroke, Style } from 'ol/style'

export const spreadInDirection = (
  feature: Feature,
  direction: 'north' | 'south' | 'east' | 'west',
  distance: number
): VectorLayer[] => {
  const shiftedPolygon = shiftPolygonBoundingBox(feature, direction, distance)

  // Create styles for the original polygon and shifted bounding box
  const originalFeatureStyle = new Style({
    fill: new Fill({
      color: 'rgba(255, 0, 0, 0.5)' // Red fill for the original feature
    }),
    stroke: new Stroke({
      color: '#ff0000',
      width: 2
    })
  })

  const spreadFeatureStyle = new Style({
    fill: new Fill({
      color: 'rgba(249, 222, 0, 0.4)' // Light orange for spread feature
    }),
    stroke: new Stroke({
      color: '#ff7400',
      width: 2
    })
  })

  // Add the original polygon layer
  const originalFeatureSource = new VectorSource({
    features: new GeoJSON().readFeatures(feature, {
      featureProjection: 'EPSG:3857' // Match the map's projection
    })
  })

  const originalFeatureLayer = new VectorLayer({
    source: originalFeatureSource,
    style: originalFeatureStyle
  })

  // Add the shifted bounding box to the map
  const spreadFeatureSource = new VectorSource({
    features: new GeoJSON().readFeatures(shiftedPolygon, {
      featureProjection: 'EPSG:3857'
    })
  })

  const spreadFeatureLayer = new VectorLayer({
    source: spreadFeatureSource,
    style: spreadFeatureStyle
  })

  return [originalFeatureLayer, spreadFeatureLayer]
}

/**
 * Shift the bounding box of any polygon in a specific direction by a given distance (in meters).
 * @param feature - A GeoJSON polygon to be shifted.
 * @param direction - Direction to shift ('north', 'south', 'east', 'west').
 * @param distance - Distance to shift (in meters).
 * @returns Shifted bounding box as a GeoJSON polygon.
 */
export const shiftPolygonBoundingBox = (
  feature:
    | Point
    | MultiPoint
    | LineString
    | MultiLineString
    | Polygon
    | MultiPolygon
    | Feature<Geometry, GeoJsonProperties>,
  direction: 'north' | 'south' | 'east' | 'west',
  distance: number
) => {
  // Get the bounding box of the input polygon in degrees (EPSG:4326)
  const bb = bbox(feature)

  // Convert the corners of the bounding box to meters (EPSG:3857)
  const minPoint = fromLonLat([bb[0], bb[1]]) // minX, minY (bottom-left)
  const maxPoint = fromLonLat([bb[2], bb[3]]) // maxX, maxY (top-right)

  let shiftedMinPoint = [...minPoint]
  let shiftedMaxPoint = [...maxPoint]

  // Apply the shift based on the direction
  switch (direction) {
    case 'north':
      shiftedMinPoint[1] += distance
      shiftedMaxPoint[1] += distance
      break
    case 'south':
      shiftedMinPoint[1] -= distance
      shiftedMaxPoint[1] -= distance
      break
    case 'east':
      shiftedMinPoint[0] += distance
      shiftedMaxPoint[0] += distance
      break
    case 'west':
      shiftedMinPoint[0] -= distance
      shiftedMaxPoint[0] -= distance
      break
    default:
      console.error('Invalid direction. Use north, south, east, or west.')
      return null
  }

  // Convert the shifted points back to degrees (EPSG:4326)
  const shiftedMinLonLat = toLonLat(shiftedMinPoint)
  const shiftedMaxLonLat = toLonLat(shiftedMaxPoint)

  // Create a new bounding box in lon/lat degrees
  const shiftedBbox = [
    shiftedMinLonLat[0], // minX (longitude)
    shiftedMinLonLat[1], // minY (latitude)
    shiftedMaxLonLat[0], // maxX (longitude)
    shiftedMaxLonLat[1] // maxY (latitude)
  ]

  // Construct a GeoJSON polygon from the shifted bounding box
  const shiftedBboxPolygon = polygon([
    [
      [shiftedBbox[0], shiftedBbox[1]], // Bottom-left
      [shiftedBbox[2], shiftedBbox[1]], // Bottom-right
      [shiftedBbox[2], shiftedBbox[3]], // Top-right
      [shiftedBbox[0], shiftedBbox[3]], // Top-left
      [shiftedBbox[0], shiftedBbox[1]] // Close the polygon (back to bottom-left)
    ]
  ])

  return shiftedBboxPolygon
}
