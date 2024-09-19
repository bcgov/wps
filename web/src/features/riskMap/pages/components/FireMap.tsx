import React, { useEffect, useRef, useState } from 'react'
import 'ol/ol.css'
import { Feature, Map, View } from 'ol'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import { fromLonLat, toLonLat } from 'ol/proj'
import { BC_EXTENT, CENTER_OF_BC } from '@/utils/constants'
import { Fill, Style, Text, Stroke } from 'ol/style'
import { Select } from 'ol/interaction'
import firePerimeterData from './PROT_CURRENT_FIRE_POLYS_SP.json'
import hotspots from './FirespotArea_canada_c6.1_48.json'
import { boundingExtent } from 'ol/extent'
import { Point } from 'ol/geom'
import { point, distance } from '@turf/turf'
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material'

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const findLayerByName = (map: Map, layerName: string): VectorLayer | undefined => {
  const layers = map.getLayers().getArray()
  return layers.find(layer => layer.get('layerName') === layerName) as VectorLayer | undefined
}

export interface FireMapProps {
  valuesFile: File | null
  setMapInstance: React.Dispatch<React.SetStateAction<Map | null>>
}

export const FireMap: React.FC<FireMapProps> = ({ valuesFile, setMapInstance }: FireMapProps) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<Map | null>(null)
  const [open, setOpen] = useState(false)
  const [closestDistance, setClosestDistance] = useState<number | null>(null)

  useEffect(() => {
    if (valuesFile && mapInstanceRef.current) {
      const reader = new FileReader()

      reader.onload = e => {
        if (e.target && e.target.result) {
          try {
            const geojsonData = JSON.parse(e.target.result as string)

            const vectorSource = new VectorSource({
              features: new GeoJSON().readFeatures(geojsonData, {
                featureProjection: 'EPSG:3857'
              })
            })

            const vectorLayer = new VectorLayer({
              source: vectorSource
            })

            mapInstanceRef.current?.addLayer(vectorLayer)
          } catch (error) {
            console.error('Error parsing GeoJSON data:', error)
          }
        }
      }

      reader.readAsText(valuesFile)
    }
  }, [valuesFile, mapInstanceRef.current])

  useEffect(() => {
    if (!mapInstanceRef.current) {
      const firePerimeterStyler = (feature: any) => {
        const labelText = feature.get('FIRE_NUMBER') || ''
        return new Style({
          fill: new Fill({
            color: 'rgba(251,171,96, 0.8)'
          }),
          text: new Text({
            font: '12px Calibri,sans-serif',
            text: labelText,
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
            style: firePerimeterStyler,
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
                color: 'rgba(255, 0, 0, 0.8)'
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

      const selectClick = new Select({
        condition: event => {
          return event.type === 'singleclick'
        }
      })

      selectClick.on('select', event => {
        if (event.selected.length > 0) {
          const feature = event.selected[0]
          const selectedGeometry = feature.getGeometry()

          if (selectedGeometry instanceof Point) {
            const selectedPointCoords = selectedGeometry.getCoordinates()
            const lonLatCoords = toLonLat(selectedPointCoords)

            const fireLayer = findLayerByName(map, 'firePerimDay4')
            const source = fireLayer!.getSource()
            const features = source!.getFeatures()

            let closestDistance = Infinity
            let closestFeature = null

            features.forEach((layerFeature: Feature) => {
              const geometry = layerFeature.getGeometry()
              if (geometry) {
                const closestPoint = geometry.getClosestPoint(selectedPointCoords)
                const closestPointLonLat = toLonLat(closestPoint)

                const turfPointA = point(lonLatCoords)
                const turfPointB = point(closestPointLonLat)

                const dist = distance(turfPointA, turfPointB, { units: 'kilometers' })

                if (dist < closestDistance) {
                  closestDistance = dist
                  closestFeature = layerFeature
                }
              }
            })

            if (closestFeature) {
              setClosestDistance(closestDistance)
              setOpen(true) // Open the dialog
            }
          } else {
            console.error('Selected feature is not a point geometry.')
          }
        }
      })

      mapInstanceRef.current = map
      setMapInstance(map)
      map.addInteraction(selectClick)
    }
  }, [])

  const handleClose = () => {
    setOpen(false)
    setClosestDistance(null)
  }

  return (
    <>
      <div ref={mapRef} style={{ width: '1800px', height: '800px' }} />
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Closest Distance</DialogTitle>
        <DialogContent>
          {closestDistance !== null ? (
            <p>Closest Distance: {closestDistance.toPrecision(2)} km</p>
          ) : (
            <p>No distance calculated.</p>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
