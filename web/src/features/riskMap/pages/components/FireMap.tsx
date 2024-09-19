import React, { useEffect, useRef } from 'react'
import 'ol/ol.css'
import { Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat } from 'ol/proj'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Fill, Style, Text, Stroke } from 'ol/style'

import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './FirespotArea_canada_c6.1_48.json'
import { boundingExtent } from 'ol/extent'

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

export interface FireMapProps {
  valuesFile: File | null
  setMapInstance: React.Dispatch<React.SetStateAction<Map | null>>
}

export const FireMap: React.FC<FireMapProps> = ({ valuesFile, setMapInstance }: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  useEffect(() => {
    if (valuesFile && mapInstanceRef.current) {
      const reader = new FileReader()

      reader.onload = e => {
        if (e.target && e.target.result) {
          try {
            const geojsonData = JSON.parse(e.target.result as string) // Parse the file content as JSON

            const vectorSource = new VectorSource({
              features: new GeoJSON().readFeatures(geojsonData, {
                featureProjection: 'EPSG:3857' // Ensure the correct projection
              })
            })

            const vectorLayer = new VectorLayer({
              source: vectorSource
            })

            // Add the vector layer to the map
            mapInstanceRef.current?.addLayer(vectorLayer)
          } catch (error) {
            console.error('Error parsing GeoJSON data:', error)
          }
        }
      }

      reader.readAsText(valuesFile) // Read the file as text
    }
  }, [valuesFile, mapInstanceRef.current])

  useEffect(() => {
    if (!mapInstanceRef.current) {
      const labelStyle = (feature: any) => {
        const labelText = feature.get('FIRE_NUMBER') || '' // Fallback to an empty string if 'name' is undefined
        return new Style({
          fill: new Fill({
            color: 'rgba(251,171,96, 0.8)' // Orange
          }),
          text: new Text({
            font: '12px Calibri,sans-serif',
            text: labelText, // Ensure it's always a string
            fill: new Fill({
              color: '#000'
            }),
            stroke: new Stroke({
              color: '#fff',
              width: 2
            })
          })
        })
      }
      const map = new Map({
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          }),
          new VectorLayer({
            style: labelStyle,
            source: new VectorSource({
              features: new GeoJSON().readFeatures(firePerimeterData, {
                featureProjection: 'EPSG:3857'
              })
            }),
            zIndex: 50
          }),
          new VectorLayer({
            style: new Style({
              fill: new Fill({
                color: 'rgba(255, 0, 0, 0.8)' // Red fill with 60% opacity
              })
            }),
            source: new VectorSource({
              features: new GeoJSON().readFeatures(hotspots, {
                featureProjection: 'EPSG:3857'
              })
            }),
            zIndex: 52
          })
        ],
        view: new View({
          center: fromLonLat(CENTER_OF_BC),
          zoom: 5
        })
      })

      map.getView().fit(bcExtent, { padding: [50, 50, 50, 50] })

      mapInstanceRef.current = map
      setMapInstance(map)
    }
  }, [])

  return <div ref={mapRef} style={{ width: '1800px', height: '800px' }} />
}
