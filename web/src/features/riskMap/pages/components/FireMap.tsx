import React, { useEffect, useRef } from 'react'
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat } from 'ol/proj'
import { CENTER_OF_BC } from '@/utils/constants'
import { Fill, Style } from 'ol/style'
import {
  Point,
  MultiPoint,
  LineString,
  MultiLineString,
  Polygon,
  MultiPolygon,
  Feature,
  Geometry,
  GeoJsonProperties,
  FeatureCollection
} from 'geojson'
import { spreadInDirection } from '@/features/riskMap/pages/components/fireSpreader'

export const FireMap: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  const loadGeoJSON = async (
    fileName: string,
    style: Style,
    spreader?: (
      feature:
        | Point
        | MultiPoint
        | LineString
        | MultiLineString
        | Polygon
        | MultiPolygon
        | Feature<Geometry, GeoJsonProperties>
    ) => VectorLayer[]
  ) => {
    try {
      const response = await fetch(fileName)
      const geojsonData: FeatureCollection = await response.json()
      const layers = spreader
        ? geojsonData.features.map(feature => spreader(feature))
        : [
            new VectorLayer({
              style,
              source: new VectorSource({
                features: new GeoJSON().readFeatures(geojsonData, {
                  featureProjection: 'EPSG:3857'
                })
              })
            })
          ]

      layers.flat().forEach(layer => mapInstanceRef.current?.addLayer(layer))
    } catch (error) {
      console.error('Error loading GeoJSON data:', error)
    }
  }

  useEffect(() => {
    if (!mapInstanceRef.current) {
      const map = new Map({
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          })
        ],
        view: new View({
          center: fromLonLat(CENTER_OF_BC),
          zoom: 5
        })
      })
      mapInstanceRef.current = map

      loadGeoJSON(
        '/PROT_CURRENT_FIRE_POLYS_SP.geojson',
        new Style({
          fill: new Fill({
            color: 'rgba(0, 0, 255, 0.6)' // Blue fill with 60% opacity
          })
        })
      )
      loadGeoJSON(
        '/FirespotArea_canada_c6.1_48.geojson',
        new Style({
          fill: new Fill({
            color: 'rgba(255, 0, 0, 0.6)' // Red fill with 60% opacity
          })
        }),
        feature => spreadInDirection(feature, 'north', 1000)
      )
    }
  }, [])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
