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
import axios from 'api/axios'

import { GrowControl } from '@/features/riskMap/pages/components/GrowControl'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './FirespotArea_canada_c6.1_48.json'

export interface FireMapProps {
  valuesFile: File | null
}

export const FireMap: React.FC<FireMapProps> = ({ valuesFile }: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)

  const getRandomColor = () => {
    const r = Math.floor(Math.random() * 256) // Random red value
    const g = Math.floor(Math.random() * 256) // Random green value
    const b = Math.floor(Math.random() * 256) // Random blue value
    const a = 0.6 // Fixed alpha for transparency (60% opacity)
    return `rgba(${r}, ${g}, ${b}, ${a})`
  }

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
    console.log(firePerimeterData)
    console.log(hotspots)
    if (!mapInstanceRef.current) {
      const map = new Map({
        target: mapRef.current!,
        layers: [
          new TileLayer({
            source: new OSM()
          }),
          new VectorLayer({
            style: new Style({
              fill: new Fill({
                color: 'rgba(0, 0, 255, 0.8)' // Blue fill with 60% opacity
              })
            }),
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

      // Method to trigger the fetch request
      const growFire = async () => {
        try {
          const url = 'risk-map/grow'
          const { data } = await axios.post(url, {
            fire_perimeter: {
              // @ts-ignore
              features: firePerimeterData.features
            },
            hotspots: {
              features: hotspots.features
            }
          })

          // Set the initial zIndex to a high value
          let initialZIndex = 45

          data.forEach((firePerimeterDataItem: any) => {
            const firePerimeterLayer = new VectorLayer({
              style: new Style({
                fill: new Fill({
                  color: getRandomColor()
                })
              }),
              source: new VectorSource({
                features: new GeoJSON().readFeatures(firePerimeterDataItem, {
                  featureProjection: 'EPSG:3857'
                })
              })
            })

            // Set a decreasing zIndex for each layer
            firePerimeterLayer.setZIndex((initialZIndex -= 1))

            // Add the layer to the map
            map.addLayer(firePerimeterLayer)
          })
        } catch (error) {
          console.error('Error fetching data:', error)
        }
      }

      map.addControl(new GrowControl({ apiCallback: growFire }))

      mapInstanceRef.current = map
    }
  }, [])

  return <div ref={mapRef} style={{ width: '1000px', height: '1000px' }} />
}
