import React, { useEffect, useRef } from 'react'
import { Box } from '@mui/material'
import { Feature, Map, MapBrowserEvent, View } from 'ol'
import { boundingExtent } from 'ol/extent'
import { Point } from 'ol/geom'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import 'ol/ol.css'
import { fromLonLat, toLonLat } from 'ol/proj'
import VectorSource from 'ol/source/Vector'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'
import { BC_EXTENT, CENTER_OF_BC } from '@wps/utils/constants'
import { source as baseMapSource } from '@/features/fireWeather/components/maps/constants'

interface SpotRequestLocation {
  latitude: number
  longitude: number
}

interface SpotRequestLocationMapProps {
  value: SpotRequestLocation | null
  onChange: (value: SpotRequestLocation | null) => void
}

const bcExtent = boundingExtent(BC_EXTENT.map(coord => fromLonLat(coord)))

const markerStyle = new Style({
  image: new CircleStyle({
    radius: 7,
    fill: new Fill({ color: '#d32f2f' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 })
  })
})

const SpotRequestLocationMap: React.FC<SpotRequestLocationMapProps> = ({ value, onChange }) => {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const featureSourceRef = useRef(new VectorSource<Feature<Point>>())
  const onChangeRef = useRef(onChange)

  useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  useEffect(() => {
    if (!mapRef.current) {
      return
    }

    const featureLayer = new VectorLayer({
      source: featureSourceRef.current,
      style: markerStyle,
      zIndex: 50
    })

    const mapObject = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({
          source: baseMapSource
        }),
        featureLayer
      ],
      view: new View({
        zoom: 5,
        center: fromLonLat(CENTER_OF_BC)
      })
    })

    mapObject.getView().fit(bcExtent, { padding: [30, 30, 30, 30] })

    mapObject.on('singleclick', (event: MapBrowserEvent<UIEvent>) => {
      const [longitude, latitude] = toLonLat(event.coordinate)
      onChangeRef.current({
        latitude: Number(latitude.toFixed(6)),
        longitude: Number(longitude.toFixed(6))
      })
    })

    return () => {
      mapObject.setTarget('')
    }
  }, [])

  useEffect(() => {
    featureSourceRef.current.clear()

    if (value) {
      featureSourceRef.current.addFeature(
        new Feature({
          geometry: new Point(fromLonLat([value.longitude, value.latitude]))
        })
      )
    }
  }, [value])

  return <Box ref={mapRef} sx={{ width: '100%', height: 320, border: '1px solid', borderColor: 'divider' }} />
}

export default SpotRequestLocationMap
