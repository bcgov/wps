import React, { useRef, useEffect } from 'react'
import { selectCHaines } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { makeStyles } from '@material-ui/core/styles'
import FormControl from '@material-ui/core/FormControl'
import Select from '@material-ui/core/Select'
import { fetchModelRuns } from 'features/cHaines/slices/cHainesSlice'
import { Container, PageHeader, PageTitle } from 'components'
import { MenuItem } from '@material-ui/core'

const useStyles = makeStyles({
  map: {
    height: '640px'
  }
})

// interface CHainesPageProps

const CHainesPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const mapRef = useRef<L.Map | null>(null)
  const { model_runs } = useSelector(selectCHaines)

  useEffect(() => {
    dispatch(fetchModelRuns())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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

  const handleChange = (
    event: React.ChangeEvent<{ name?: string | undefined; value: unknown }>
  ) => {
    console.log(event.target.value)
    // TODO: ok - load the predictions
    // TODO: ok - loop through them
  }

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="C-Haines" />
      <PageTitle title="C-Haines" />
      <Container>
        <div id="map-with-selectable-wx-stations" className={classes.map} />
        {model_runs.map((model_run, i) => (
          <div key={i}>{model_run.model_run_timestamp}</div>
        ))}
        Model run:
        <FormControl>
          <Select
            defaultValue={model_runs.length > 0 ? model_runs[0].model_run_timestamp : ''}
            onChange={handleChange}
          >
            {model_runs.map((model_run, i) => (
              <option value={model_run.model_run_timestamp} key={i}>
                {model_run.model_run_timestamp}
              </option>
            ))}
          </Select>
        </FormControl>
      </Container>
    </main>
  )
}

export default React.memo(CHainesPage)
