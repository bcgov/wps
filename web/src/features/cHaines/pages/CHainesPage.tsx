import React, { useRef, useEffect, useState } from 'react'
import ReactDOMServer from 'react-dom/server'
import { selectCHainesModelRuns } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { tiledMapLayer } from 'esri-leaflet'
import { makeStyles } from '@material-ui/core/styles'
import { FeatureCollection } from 'geojson'
import {
  fetchModelRuns,
  updateSelectedModel,
  updateSelectedPrediction,
  fetchCHainesGeoJSON
} from 'features/cHaines/slices/cHainesModelRunsSlice'
import { Container, PageHeader, PageTitle } from 'components'
import { formatDateInPDT } from 'utils/date'

const useStyles = makeStyles({
  map: {
    height: '640px'
  },
  legend: {
    display: 'flex',
    backgroundColor: 'white'
  },
  description: {
    paddingLeft: 10,
    paddingRight: 10
  },
  loading: {
    backgroundColor: 'white',
    opacity: 0.8,
    width: '100%'
  },
  label: {
    backgroundColor: 'white',
    opacity: 0.8
  },
  extreme: {
    backgroundColor: '#ff0000',
    width: 30,
    height: 30
  },
  high: {
    backgroundColor: '#FFA500',
    width: 30,
    height: 30
  },
  moderate: {
    backgroundColor: '#ffff00',
    width: 30,
    height: 30
  }
})

// interface CHainesPageProps

const CHainesPage = () => {
  const classes = useStyles()
  const dispatch = useDispatch()
  const mapRef = useRef<L.Map | null>(null)
  const layersRef = useRef<Record<string, L.GeoJSON>>({})
  const mapTitleRef = useRef<L.Control | null>(null)
  const loadingLayerRef = useRef<L.Control | null>(null)
  const currentLayersRef = useRef<L.GeoJSON | null>(null)
  const loopTimeoutRef = useRef<number | null>(null)
  const [isAnimating, setAnimate] = useState(false)
  const [animationInterval, setAnimationInterval] = useState(500)
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

  const loadModelPrediction = (
    model_run_timestamp: string,
    prediction_timestamp: string
  ) => {
    dispatch(updateSelectedPrediction(prediction_timestamp))
    if (isLoaded(model_run_timestamp, prediction_timestamp)) {
      showLayer(model_run_timestamp, prediction_timestamp)
      // if it's already loaded, we can just show it
    } else {
      // fetch the data
      dispatch(fetchCHainesGeoJSON(model_run_timestamp, prediction_timestamp))
    }
  }

  const isLoaded = (model_run_timestamp: string, prediction_timestamp: string) => {
    return (
      model_run_timestamp in model_run_predictions &&
      prediction_timestamp in model_run_predictions[model_run_timestamp]
    )
  }

  useEffect(() => {
    dispatch(fetchModelRuns())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selected_prediction && selected_model && model_runs.length > 0) {
      loadModelPrediction(selected_model, selected_prediction)
    }
  }, [model_runs])

  useEffect(() => {
    if (selected_model in model_run_predictions) {
      if (selected_prediction in model_run_predictions[selected_model]) {
        showLayer(selected_model, selected_prediction)
      }
    }
  }, [model_run_predictions])

  useEffect(() => {
    mapRef.current = L.map('map-with-selectable-wx-stations', {
      center: [55, -123.6],
      zoom: 5,
      // scrollWheelZoom: false,
      zoomAnimation: true
      // layers: [topoLayer, stationOverlay]
    })
    L.control.scale().addTo(mapRef.current)

    const baseLayer = tiledMapLayer({
      //url:  'https://maps.gov.bc.ca/arcserver/rest/services/province/web_mercator_cache/MapServer'
      url: 'https://maps.gov.bc.ca/arcserver/rest/services/Province/roads_wm/MapServer'
    })
    baseLayer.addTo(mapRef.current)

    // Active weather stations layer.
    L.tileLayer
      .wms(
        'https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP/ows?',
        {
          format: 'image/png',
          layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP',
          styles: 'BC_Wildfire_Active_Weather_Stations',
          transparent: true,
          minZoom: 0,
          maxZoom: 18
        }
      )
      .addTo(mapRef.current)

    // Active weather station labels.
    L.tileLayer
      .wms(
        'https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP/ows?',
        {
          format: 'image/png',
          layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP',
          styles: 'BC_Wildfire_Active_Weather_Stations_Labels',
          transparent: true,
          minZoom: 0,
          maxZoom: 18
        }
      )
      .addTo(mapRef.current)

    L.tileLayer
      .wms(
        'https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_DANGER_RATING_SP/ows?',
        {
          format: 'image/png',
          layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_DANGER_RATING_SP',
          styles: 'BC_Wildfire_Fire_Danger_Rating',
          transparent: true,
          minZoom: 0,
          maxZoom: 18
        }
      )
      .addTo(mapRef.current)

    // const streetLayer = L.tileLayer(
    //   'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    //   {
    //     attribution:
    //       '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    //   }
    // )
    // streetLayer.addTo(mapRef.current)

    // Create and add the legend.
    const customControl = L.Control.extend({
      onAdd: function(map: any) {
        const html = (
          <div>
            <div className={classes.legend}>
              <div className={classes.extreme}></div>
              <div className={classes.description}>11+ Extreme</div>
            </div>
            <div className={classes.legend}>
              <div className={classes.high}></div>
              <div className={classes.description}>8-11 High</div>
            </div>
            <div className={classes.legend}>
              <div className={classes.moderate}></div>
              <div className={classes.description}>4-8 Moderate</div>
            </div>
          </div>
        )

        const div = L.DomUtil.create('div')
        div.innerHTML = ReactDOMServer.renderToString(html)
        return div
      },

      onRemove: function(map: any) {
        //
      }
    })
    new customControl({ position: 'bottomleft' }).addTo(mapRef.current)
    // L.control.layers(baseMaps, overlays).addTo(mapRef.current)

    // const legend = L.control({position: 'bottomLeft'});

    // Destroy the map and clear all related event listeners when the component unmounts
    return () => {
      mapRef.current?.remove()
    }
  }, []) // Initialize the map only once

  useEffect(() => {
    if (mapRef.current && selected_model && selected_prediction) {
      if (isLoaded(selected_model, selected_prediction)) {
        console.log('show new layer etc.')
        const customControl = L.Control.extend({
          onAdd: function(map: any) {
            const html = (
              <div className={classes.label}>
                <div>GDPS model run: {selected_model} (UTC)</div>
                <div>GDPS prediction: {formatDateInPDT(selected_prediction)} (PDT)</div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: function(map: any) {
            //
          }
        })
        if (loadingLayerRef.current) {
          mapRef.current.removeControl(loadingLayerRef.current)
        }
        if (mapTitleRef.current) {
          mapRef.current.removeControl(mapTitleRef.current)
        }
        mapTitleRef.current = new customControl({ position: 'topright' })
        mapTitleRef.current.addTo(mapRef.current)
        if (isAnimating) {
          loopTimeoutRef.current = window.setTimeout(() => {
            loadNextPrediction()
          }, animationInterval)
        }
      } else {
        const customControl = L.Control.extend({
          onAdd: function(map: any) {
            const html = (
              <div className={classes.loading}>
                <div>LOADING: {selected_prediction} (UTC)</div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: function(map: any) {
            //
          }
        })
        if (loadingLayerRef.current) {
          mapRef.current.removeControl(loadingLayerRef.current)
        }
        loadingLayerRef.current = new customControl({ position: 'topright' })
        loadingLayerRef.current.addTo(mapRef.current)
      }
    }
  }, [
    selected_model,
    selected_prediction,
    model_run_predictions,
    isLoaded(selected_model, selected_prediction),
    isAnimating
  ])

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

  const handleChangeModel = (
    event: React.ChangeEvent<{ name?: string | undefined; value: string }>
  ) => {
    console.log('handleChangeModel', event.target.value)
    dispatch(updateSelectedModel(event.target.value))
  }

  const handlePredictionChange = (
    event: React.ChangeEvent<{ name?: string | undefined; value: string }>
  ) => {
    console.log('handlePredictionChange')
    loadModelPrediction(selected_model, event.target.value)
  }

  const handleIntervalChange = (
    event: React.ChangeEvent<{ name?: string | undefined; value: string }>
  ) => {
    setAnimationInterval(Number(event.target.value))
  }

  const loadAllModelsPredictions = () => {
    model_runs.forEach(modelRun => {
      modelRun.prediction_timestamps.forEach(prediction_timestamp => {
        dispatch(fetchCHainesGeoJSON(modelRun.model_run_timestamp, prediction_timestamp))
      })
    })
  }

  const loadNextPrediction = () => {
    const model_run = model_runs.find(
      model_run => model_run.model_run_timestamp === selected_model
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.findIndex(
        value => value === selected_prediction
      )
      const nextIndex = index + 1 < model_run.prediction_timestamps.length ? index + 1 : 0
      loadModelPrediction(selected_model, model_run.prediction_timestamps[nextIndex])
    }
  }

  const loadPreviousPrediction = () => {
    const model_run = model_runs.find(
      model_run => model_run.model_run_timestamp === selected_model
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.findIndex(
        value => value === selected_prediction
      )
      const nextIndex = index > 0 ? index - 1 : model_run.prediction_timestamps.length - 1
      loadModelPrediction(selected_model, model_run.prediction_timestamps[nextIndex])
    }
  }

  const toggleAnimate = () => {
    const animate = !isAnimating
    setAnimate(animate)
    if (animate) {
      loadNextPrediction()
    } else {
      if (loopTimeoutRef.current) {
        window.clearTimeout(loopTimeoutRef.current)
      }
    }
  }

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="C-Haines" />
      <PageTitle title="C-Haines" />
      <Container>
        <div id="map-with-selectable-wx-stations" className={classes.map} />
        <div>
          <div>Select a model run and prediction from the dropdown:</div>
          <div>
            Model runs:
            <select value={selected_model} onChange={handleChangeModel}>
              {model_runs.map((model_run, i) => (
                <option value={model_run.model_run_timestamp} key={i}>
                  GDPS {model_run.model_run_timestamp} (UTC)
                </option>
              ))}
            </select>
          </div>
          <div>
            Predictions:
            <select value={selected_prediction} onChange={handlePredictionChange}>
              {model_runs
                .filter(model_run => {
                  return model_run.model_run_timestamp === selected_model
                })
                .map((model_run, i) =>
                  model_run.prediction_timestamps.map((prediction_timestamp, i2) => (
                    <option key={`${i}-${i2}`} value={prediction_timestamp}>
                      {/* {prediction_timestamp} (UTC) */}
                      {formatDateInPDT(prediction_timestamp)} (PDT)
                    </option>
                  ))
                )}
            </select>
          </div>
          {/* <div>
            (current: GDPS {selected_model} : {selected_prediction}) :{' '}
            {isLoaded(selected_model, selected_prediction) ? 'Loaded' : 'Loading'}
          </div> */}
          <div>
            <button onClick={() => loadPreviousPrediction()}>Prev</button>
            <button onClick={() => toggleAnimate()}>
              {isAnimating ? 'Stop' : 'Animate'}
            </button>
            <button onClick={() => loadNextPrediction()}>Next</button>
          </div>
          <div>
            Animation interval:{' '}
            <select value={animationInterval} onChange={handleIntervalChange}>
              <option value="1">1ms</option>
              <option value="100">100ms</option>
              <option value="500">500ms</option>
              <option value="1000">1s</option>
              <option value="5000">5s</option>
            </select>
          </div>
        </div>
        <div>
          <div>
            <br />
            <br />
            <br />
            Don't mess with this the stuff down here!
          </div>
          <div>
            <button onClick={() => loadAllModelsPredictions()}>Load all</button>
          </div>
          {/* <div>
            <button onClick={() => animate(0)}>Animate</button>
          </div> */}
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
        </div>
      </Container>
    </main>
  )
}

export default React.memo(CHainesPage)
