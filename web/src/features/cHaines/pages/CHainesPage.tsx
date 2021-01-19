import React, { useRef, useEffect } from 'react'
import { selectCHainesModelRuns } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { makeStyles } from '@material-ui/core/styles'
import {
  fetchModelRuns,
  updateSelectedModel,
  updateSelectedPrediction,
  fetchCHainesGeoJSON
} from 'features/cHaines/slices/cHainesModelRunsSlice'
import { Container, PageHeader, PageTitle } from 'components'
import { FeatureCollection } from 'geojson'

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
  const layersRef = useRef<Record<string, L.GeoJSON>>({})
  const currentLayersRef = useRef<L.GeoJSON | null>(null)
  const {
    model_runs,
    selected_model,
    model_run_predictions,
    selected_prediction
  } = useSelector(selectCHainesModelRuns)
  // const {} = useSelector(selectChainesPredictions)
  // const [selectedModel, setSelectedModel] = useState(
  //   model_runs.length > 0 ? model_runs[0].model_run_timestamp : ''
  // )

  useEffect(() => {
    dispatch(fetchModelRuns())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const createLayer = (data: FeatureCollection) => {
    return L.geoJSON(data, {
      style: feature => {
        switch (feature?.properties.severity) {
          case 1:
            // yellow
            return { color: '#ffff00' }
          case 2:
            return { color: '#FFA500' }
          case 3:
            // red
            return { color: '#ff0000' }
          // return { color: "#800080" }; // purple
          default:
            return {}
        }
      }
    })
  }

  const getLayer = (selected_model: string, selected_prediction: string) => {
    const layerKey = `${selected_model}-${selected_prediction}`
    if (layerKey in layersRef.current) {
      return layersRef.current[layerKey]
    } else {
      const data = model_run_predictions[selected_model][selected_prediction]
      const geoJsonLayer = createLayer(data)
      layersRef.current[layerKey] = geoJsonLayer
      return geoJsonLayer
    }
  }

  const showLayer = (selected_model: string, selected_prediction: string) => {
    const geoJsonLayer = getLayer(selected_model, selected_prediction)
    if (mapRef.current) {
      if (currentLayersRef.current) {
        mapRef.current.removeLayer(currentLayersRef.current)
        currentLayersRef.current = null
      }
      geoJsonLayer.addTo(mapRef.current)
      currentLayersRef.current = geoJsonLayer
    }
  }

  useEffect(() => {
    if (selected_model in model_run_predictions) {
      if (selected_prediction in model_run_predictions[selected_model]) {
        console.log('have new model run prediction!', selected_model, selected_prediction)
        showLayer(selected_model, selected_prediction)
      }
    }
  }, [model_run_predictions])

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
    event: React.ChangeEvent<{ name?: string | undefined; value: string }>
  ) => {
    console.log(event.target.value)
    dispatch(updateSelectedModel(event.target.value))
  }

  const isLoaded = (model_run_timestamp: string, prediction_timestamp: string) => {
    return (
      model_run_timestamp in model_run_predictions &&
      prediction_timestamp in model_run_predictions[model_run_timestamp]
    )
  }

  const loadModelPrediction = (
    model_run_timestamp: string,
    prediction_timestamp: string
  ) => {
    console.log('load', model_run_timestamp, prediction_timestamp)
    dispatch(updateSelectedPrediction(prediction_timestamp))
    if (isLoaded(model_run_timestamp, prediction_timestamp)) {
      showLayer(model_run_timestamp, prediction_timestamp)
      // if it's already loaded, we can just show it
    } else {
      // fetch the data
      dispatch(fetchCHainesGeoJSON(model_run_timestamp, prediction_timestamp))
    }
  }

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="C-Haines" />
      <PageTitle title="C-Haines" />
      <Container>
        <div id="map-with-selectable-wx-stations" className={classes.map} />
        Model runs:
        <select defaultValue={selected_model} onChange={handleChange}>
          {model_runs.map((model_run, i) => (
            <option value={model_run.model_run_timestamp} key={i}>
              {model_run.model_run_timestamp}
            </option>
          ))}
        </select>
        (current: {selected_model})
        {model_runs
          .filter(model_run => {
            return model_run.model_run_timestamp === selected_model
          })
          .map((model_run, i) =>
            model_run.prediction_timestamps.map((prediction_timestamp, i2) => (
              <div key={`${i}-${i2}`}>
                <button
                  onClick={() =>
                    loadModelPrediction(
                      model_run.model_run_timestamp,
                      prediction_timestamp
                    )
                  }
                >
                  {prediction_timestamp}
                </button>
                {isLoaded(model_run.model_run_timestamp, prediction_timestamp)
                  ? 'Loaded'
                  : ''}
                {/* {model_run.model_run_timestamp in model_run_predictions &&
                prediction_timestamp in
                  model_run_predictions[model_run.model_run_timestamp]
                  ? 'Loaded'
                  : ''} */}
              </div>
            ))
          )}
      </Container>
    </main>
  )
}

export default React.memo(CHainesPage)
