import React, { useRef, useEffect } from 'react'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { makeStyles } from '@material-ui/core/styles'

import { Container, PageHeader, PageTitle } from 'components'

const useStyles = makeStyles({
  map: {
    height: '640px'
  }
})

interface Props {}

const CHainesPage: React.FunctionComponent<Props> = ({}: Props) => {
  const classes = useStyles()
  const mapRef = useRef<L.Map | null>(null)
  useEffect(() => {
    mapRef.current = L.map('map-with-selectable-wx-stations', {
      center: [0, 0],
      zoom: 2,
      // scrollWheelZoom: false,
      zoomAnimation: true
      // layers: [topoLayer, stationOverlay]
    })
    const streetLayer = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution:
          '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
      }
    )
    streetLayer.addTo(mapRef.current)
    // L.control.layers(baseMaps, overlays).addTo(mapRef.current)

    // Destroy the map and clear all related event listeners when the component unmounts
    return () => {
      mapRef.current?.remove()
    }
  }, []) // Initialize the map only once

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="C-Haines" />
      <PageTitle title="C-Haines" />
      <Container>
        <div id="map-with-selectable-wx-stations" className={classes.map} />
      </Container>
    </main>
  )
}

export default React.memo(CHainesPage)
