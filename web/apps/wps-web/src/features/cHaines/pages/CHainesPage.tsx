import { styled } from '@mui/material/styles'
import { selectCHainesModelRuns } from 'app/rootReducer'
import React, { useCallback, useEffect, useRef, useState } from 'react'
import ReactDOMServer from 'react-dom/server'
import { useDispatch, useSelector } from 'react-redux'
import 'leaflet/dist/leaflet.css'
import {
  getCHainesGeoJSONURI,
  getCHainesKMLModelRunURI,
  getCHainesKMLURI,
  getCHainesModelKMLURI,
  getKMLNetworkLinkURI
} from '@wps/api/cHainesAPI'
import { Container } from '@wps/ui/Container'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { C_HAINES_DOC_TITLE, C_HAINES_NAME } from '@wps/utils/constants'
import { formatDatetimeInPST } from '@wps/utils/date'
import { logError } from '@wps/utils/error'
import type { AppDispatch } from 'app/store'
import { tiledMapLayer } from 'esri-leaflet'
import {
  fetchCHainesGeoJSON,
  fetchModelRuns,
  updateSelectedModel,
  updateSelectedModelRun,
  updateSelectedPrediction
} from 'features/cHaines/slices/cHainesModelRunsSlice'
import type { FeatureCollection } from 'geojson'
import L from 'leaflet'

const PREFIX = 'CHainesPage'

const classes = {
  map: `${PREFIX}-map`,
  legend: `${PREFIX}-legend`,
  description: `${PREFIX}-description`,
  loading: `${PREFIX}-loading`,
  label: `${PREFIX}-label`,
  extreme: `${PREFIX}-extreme`,
  high: `${PREFIX}-high`,
  moderate: `${PREFIX}-moderate`,
  controls: `${PREFIX}-controls`,
  kml_links: `${PREFIX}-kml_links`,
  animateButton: `${PREFIX}-animateButton`
}

const Root = styled('main')({
  [`& .${classes.map}`]: {
    height: '640px'
  },
  [`& .${classes.legend}`]: {
    display: 'flex',
    backgroundColor: 'white'
  },
  [`& .${classes.description}`]: {
    paddingLeft: 10,
    paddingRight: 10
  },
  [`& .${classes.loading}`]: {
    backgroundColor: 'white',
    opacity: 0.8,
    width: '100%'
  },
  [`& .${classes.label}`]: {
    backgroundColor: 'white',
    opacity: 0.8
  },
  [`& .${classes.extreme}`]: {
    backgroundColor: '#ff0000',
    width: 30,
    height: 30
  },
  [`& .${classes.high}`]: {
    backgroundColor: '#FFA500',
    width: 30,
    height: 30
  },
  [`& .${classes.moderate}`]: {
    backgroundColor: '#ffff00',
    width: 30,
    height: 30
  },
  [`& .${classes.controls}`]: {
    display: 'flex'
  },
  [`& .${classes.kml_links}`]: {
    marginLeft: '10px'
  },
  [`& .${classes.animateButton}`]: {
    width: '70px'
  }
})

const createLayer = (data: FeatureCollection) => {
  const defaults = {
    fillOpacity: 0.5,
    weight: 2
  }
  return L.geoJSON(data, {
    style: feature => {
      switch (feature?.properties.c_haines_index) {
        case '4-8':
          return { ...defaults, color: '#ffff00' }
        case '8-11':
          return { ...defaults, color: '#FFA500' }
        case '>11':
          return { ...defaults, color: '#ff0000' }
        default:
          return {}
      }
    }
  })
}

// interface CHainesPageProps

const CHainesPage = () => {
  const dispatch: AppDispatch = useDispatch()
  const mapRef = useRef<L.Map | null>(null)
  const layersRef = useRef<Record<string, L.GeoJSON>>({})
  const mapTitleRef = useRef<L.Control | null>(null)
  const loadingLayerRef = useRef<L.Control | null>(null)
  const currentLayersRef = useRef<L.GeoJSON | null>(null)
  const loopTimeoutRef = useRef<number | null>(null)
  const [isAnimating, setAnimate] = useState(false)
  // Set the default animation speed to 200ms.
  const [animationInterval, setAnimationInterval] = useState(200)
  const [selectedDatetime, setSelectedDateTime] = useState(() => {
    const d = new Date()
    const month = `${d.getMonth() + 1}`
    const date = `${d.getDate()}`
    const hours = `${d.getHours()}`
    const minutes = `${d.getMinutes()}`
    return `${d.getFullYear()}-${month.padStart(2, '0')}-${date.padStart(2, '0')}T${hours.padStart(
      2,
      '0'
    )}:${minutes.padStart(2, '0')}`
  })
  const {
    model_runs,
    selected_model_run_timestamp,
    model_run_predictions,
    selected_prediction_timestamp,
    selected_model_abbreviation
  } = useSelector(selectCHainesModelRuns)

  // Refs for mutable Redux/component state read inside effects or stable callbacks
  const selectedDatetimeRef = useRef(selectedDatetime)
  selectedDatetimeRef.current = selectedDatetime
  const model_runsRef = useRef(model_runs)
  model_runsRef.current = model_runs
  const model_run_predictionsRef = useRef(model_run_predictions)
  model_run_predictionsRef.current = model_run_predictions
  const selected_prediction_timestampRef = useRef(selected_prediction_timestamp)
  selected_prediction_timestampRef.current = selected_prediction_timestamp
  const selected_model_run_timestampRef = useRef(selected_model_run_timestamp)
  selected_model_run_timestampRef.current = selected_model_run_timestamp
  const selected_model_abbreviationRef = useRef(selected_model_abbreviation)
  selected_model_abbreviationRef.current = selected_model_abbreviation
  const animationIntervalRef = useRef(animationInterval)
  animationIntervalRef.current = animationInterval

  const isLoaded = useCallback(
    (model_abbreviation: string, model_run_timestamp: string, prediction_timestamp: string) => {
      const mrp = model_run_predictionsRef.current
      return (
        model_abbreviation in mrp &&
        model_run_timestamp in mrp[model_abbreviation] &&
        prediction_timestamp in mrp[model_abbreviation][model_run_timestamp]
      )
    },
    []
  )

  const getLayer = useCallback((model: string, model_timestamp: string, prediction_timestamp: string) => {
    const mrp = model_run_predictionsRef.current
    const layerKey = `${model}-${model_timestamp}-${prediction_timestamp}`
    if (layerKey in layersRef.current) {
      return layersRef.current[layerKey]
    }
    const data = mrp[model][model_timestamp][prediction_timestamp]
    const geoJsonLayer = createLayer(data)
    layersRef.current[layerKey] = geoJsonLayer
    return geoJsonLayer
  }, [])

  const showLayer = useCallback(
    (model: string, model_run_timestamp: string, prediction_timestamp: string) => {
      try {
        const geoJsonLayer = getLayer(model, model_run_timestamp, prediction_timestamp)
        if (mapRef.current) {
          if (currentLayersRef.current) {
            mapRef.current.removeLayer(currentLayersRef.current)
            currentLayersRef.current = null
          }
          geoJsonLayer.addTo(mapRef.current)
          currentLayersRef.current = geoJsonLayer
        }
      } catch (exception) {
        // For some reason, the API sometimes returns geojson data with no features (maybe they're in the
        // process of being inserted?)
        logError(exception)
      }
    },
    [getLayer]
  )

  const loadModelPrediction = useCallback(
    (model_abbreviation: string, model_run_timestamp: string, prediction_timestamp: string) => {
      dispatch(updateSelectedPrediction(prediction_timestamp))
      if (isLoaded(model_abbreviation, model_run_timestamp, prediction_timestamp)) {
        showLayer(model_abbreviation, model_run_timestamp, prediction_timestamp)
      } else {
        dispatch(fetchCHainesGeoJSON(model_abbreviation, model_run_timestamp, prediction_timestamp))
      }
    },
    [dispatch, isLoaded, showLayer]
  )

  const loadNextPrediction = useCallback(() => {
    const model_runs = model_runsRef.current
    const model_run_timestamp = selected_model_run_timestampRef.current
    const model_abbreviation = selected_model_abbreviationRef.current
    const prediction_timestamp = selected_prediction_timestampRef.current
    const model_run = model_runs.find(
      instance => instance.model_run_timestamp === model_run_timestamp && instance.model.abbrev === model_abbreviation
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.indexOf(prediction_timestamp)
      const nextIndex = index + 1 < model_run.prediction_timestamps.length ? index + 1 : 0
      loadModelPrediction(model_abbreviation, model_run_timestamp, model_run.prediction_timestamps[nextIndex])
    }
  }, [loadModelPrediction])

  const loadPreviousPrediction = useCallback(() => {
    const model_runs = model_runsRef.current
    const model_run_timestamp = selected_model_run_timestampRef.current
    const model_abbreviation = selected_model_abbreviationRef.current
    const prediction_timestamp = selected_prediction_timestampRef.current
    const model_run = model_runs.find(
      instance => instance.model_run_timestamp === model_run_timestamp && instance.model.abbrev === model_abbreviation
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.indexOf(prediction_timestamp)
      const nextIndex = index > 0 ? index - 1 : model_run.prediction_timestamps.length - 1
      loadModelPrediction(model_abbreviation, model_run_timestamp, model_run.prediction_timestamps[nextIndex])
    }
  }, [loadModelPrediction])

  useEffect(() => {
    dispatch(fetchModelRuns(selectedDatetimeRef.current))
  }, [dispatch])

  useEffect(() => {
    const t = selected_prediction_timestampRef.current
    const mrt = selected_model_run_timestampRef.current
    const ma = selected_model_abbreviationRef.current
    if (t && mrt && model_runs.length > 0) {
      loadModelPrediction(ma, mrt, t)
    }
  }, [model_runs, loadModelPrediction])

  useEffect(() => {
    const ma = selected_model_abbreviationRef.current
    const mrt = selected_model_run_timestampRef.current
    const t = selected_prediction_timestampRef.current
    const mrp = model_run_predictions
    if (ma in mrp && mrt in mrp[ma] && t in mrp[ma][mrt]) {
      showLayer(ma, mrt, t)
    }
  }, [model_run_predictions, showLayer])

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
      .wms('https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP/ows?', {
        format: 'image/png',
        layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP',
        styles: 'BC_Wildfire_Active_Weather_Stations',
        transparent: true,
        minZoom: 0,
        maxZoom: 18
      })
      .addTo(mapRef.current)

    // Active weather station labels.
    L.tileLayer
      .wms('https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP/ows?', {
        format: 'image/png',
        layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP',
        styles: 'BC_Wildfire_Active_Weather_Stations_Labels',
        transparent: true,
        minZoom: 0,
        maxZoom: 18
      })
      .addTo(mapRef.current)

    L.tileLayer
      .wms('https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_DANGER_RATING_SP/ows?', {
        format: 'image/png',
        layers: 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_DANGER_RATING_SP',
        styles: 'BC_Wildfire_Fire_Danger_Rating',
        transparent: true,
        minZoom: 0,
        maxZoom: 18
      })
      .addTo(mapRef.current)

    // Create and add the legend.
    const customControl = L.Control.extend({
      onAdd: () => {
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

      onRemove: () => {
        //
      }
    })
    new customControl({ position: 'bottomleft' }).addTo(mapRef.current)

    // Destroy the map and clear all related event listeners when the component unmounts
    return () => {
      mapRef.current?.remove()
    }
  }, []) // Initialize the map only once

  const predictionIsLoadedCheck = isLoaded(
    selected_model_abbreviation,
    selected_model_run_timestamp,
    selected_prediction_timestamp
  )

  useEffect(() => {
    if (mapRef.current && selected_model_run_timestamp && selected_prediction_timestamp) {
      if (predictionIsLoadedCheck) {
        const customControl = L.Control.extend({
          onAdd: () => {
            const html = (
              <div className={classes.label}>
                <div>
                  {selected_model_abbreviation} model run: {selected_model_run_timestamp} (UTC)
                </div>
                <div>
                  {selected_model_abbreviation} prediction: {formatDatetimeInPST(selected_prediction_timestamp)} (PST)
                </div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: () => {
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
          onAdd: () => {
            const html = (
              <div className={classes.loading}>
                <div>LOADING: {selected_prediction_timestamp} (UTC)</div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: () => {
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
    selected_model_run_timestamp,
    selected_prediction_timestamp,
    predictionIsLoadedCheck,
    isAnimating,
    selected_model_abbreviation,
    animationInterval,
    loadNextPrediction
  ])

  const handleChangeDateTime = (event: React.ChangeEvent<{ name?: string; value: string }>) => {
    setSelectedDateTime(event.target.value)
    dispatch(fetchModelRuns(event.target.value))
  }

  const handleChangeModel = (event: React.ChangeEvent<{ name?: string; value: string }>) => {
    dispatch(updateSelectedModel(event.target.value))
    stopAnimation()
    // If the model has been changed, we need to load a different prediction.
    const model_run = model_runs.find(instance => instance.model.abbrev === event.target.value)
    if (model_run) {
      if (model_run.prediction_timestamps.length > 0) {
        loadModelPrediction(event.target.value, model_run.model_run_timestamp, model_run.prediction_timestamps[0])
      }
    }
  }

  const handleChangeModelRun = (event: React.ChangeEvent<{ name?: string; value: string }>) => {
    dispatch(updateSelectedModelRun(event.target.value))
    stopAnimation()
    // If the model run has been changed, we also have to load a different prediction.
    const model_run = model_runs.find(
      instance =>
        instance.model_run_timestamp === event.target.value && instance.model.abbrev === selected_model_abbreviation
    )
    if (model_run) {
      if (model_run.prediction_timestamps.length > 0) {
        loadModelPrediction(selected_model_abbreviation, event.target.value, model_run.prediction_timestamps[0])
      }
    }
  }

  const handlePredictionChange = (event: React.ChangeEvent<{ name?: string; value: string }>) => {
    stopAnimation()
    loadModelPrediction(selected_model_abbreviation, selected_model_run_timestamp, event.target.value)
  }

  const geoJSONURI = getCHainesGeoJSONURI(
    selected_model_abbreviation,
    selected_model_run_timestamp,
    selected_prediction_timestamp
  )

  const handleCopyClick = () => {
    const uri = getCHainesGeoJSONURI(
      selected_model_abbreviation,
      selected_model_run_timestamp,
      selected_prediction_timestamp
    )
    navigator.clipboard.writeText(uri)
  }

  const handleIntervalChange = (event: React.ChangeEvent<{ name?: string; value: string }>) => {
    setAnimationInterval(Number(event.target.value))
  }

  const stopAnimation = () => {
    setAnimate(false)
    if (loopTimeoutRef.current) {
      window.clearTimeout(loopTimeoutRef.current)
    }
  }

  const toggleAnimate = () => {
    const animate = !isAnimating
    setAnimate(animate)
    if (animate) {
      loadNextPrediction()
    } else {
      stopAnimation()
    }
  }

  const KMLNetworkLinkURL = getKMLNetworkLinkURI()

  const KMLUrl = getCHainesKMLURI(
    selected_model_abbreviation,
    selected_model_run_timestamp,
    selected_prediction_timestamp
  )

  const KMLModelUrl = getCHainesModelKMLURI(selected_model_abbreviation)

  const KMLModelRunUrl = getCHainesKMLModelRunURI(selected_model_abbreviation, selected_model_run_timestamp)

  const KMLModelFilename = `${selected_model_abbreviation}.kml`

  const KMLModelRunFilename = `${selected_model_abbreviation}-${encodeURIComponent(selected_model_run_timestamp)}.kml`

  const KMLFilename = `${selected_model_abbreviation}-${encodeURIComponent(
    selected_model_run_timestamp
  )}-${encodeURIComponent(selected_prediction_timestamp)}.kml`

  useEffect(() => {
    document.title = C_HAINES_DOC_TITLE
  }, [])

  return (
    <Root>
      <GeneralHeader isBeta={false} spacing={1} title={C_HAINES_NAME} />
      <Container sx={{ paddingTop: '1em' }} maxWidth="xl">
        <div id="map-with-selectable-wx-stations" className={classes.map} />
        <div className={classes.controls}>
          <div>
            <div>
              Date of interest:
              <input type="datetime-local" value={selectedDatetime} onChange={handleChangeDateTime}></input>
            </div>
            <div>
              Model:
              <label>
                <input
                  type="radio"
                  value="GDPS"
                  checked={selected_model_abbreviation === 'GDPS'}
                  onChange={handleChangeModel}
                />
                GDPS
              </label>
              <label>
                <input
                  type="radio"
                  value="RDPS"
                  checked={selected_model_abbreviation === 'RDPS'}
                  onChange={handleChangeModel}
                />
                RDPS
              </label>
              <label>
                <input
                  type="radio"
                  value="HRDPS"
                  checked={selected_model_abbreviation === 'HRDPS'}
                  onChange={handleChangeModel}
                />
                HRDPS
              </label>
            </div>
            <div>
              Model runs:
              {model_runs
                .filter(model_run => {
                  return model_run.model.abbrev === selected_model_abbreviation
                })
                .map(model_run => (
                  <div key={`${model_run.model.abbrev}-${model_run.model_run_timestamp}`}>
                    <label>
                      <input
                        type="radio"
                        value={model_run.model_run_timestamp}
                        checked={model_run.model_run_timestamp === selected_model_run_timestamp}
                        onChange={handleChangeModelRun}
                      />
                      {model_run.model.abbrev} {model_run.model_run_timestamp} (UTC)
                    </label>
                  </div>
                ))}
            </div>
            <div>
              Predictions:
              <select value={selected_prediction_timestamp} onChange={handlePredictionChange}>
                {model_runs
                  .filter(model_run => {
                    return (
                      model_run.model_run_timestamp === selected_model_run_timestamp &&
                      model_run.model.abbrev === selected_model_abbreviation
                    )
                  })
                  .map(model_run =>
                    model_run.prediction_timestamps.map(prediction_timestamp => (
                      <option
                        key={`${model_run.model_run_timestamp}-${prediction_timestamp}`}
                        value={prediction_timestamp}
                      >
                        {formatDatetimeInPST(prediction_timestamp)} (PST)
                      </option>
                    ))
                  )}
              </select>
            </div>
            <div>
              Animation interval:{' '}
              <select value={animationInterval} onChange={handleIntervalChange}>
                <option value="1">1ms</option>
                <option value="100">100ms</option>
                <option value="200">200ms</option>
                <option value="500">500ms</option>
                <option value="1000">1s</option>
                <option value="5000">5s</option>
              </select>
            </div>
            <div>
              <button type="button" onClick={() => loadPreviousPrediction()}>
                &lt; Prev
              </button>
              <button type="button" onClick={() => toggleAnimate()} className={classes.animateButton}>
                {isAnimating ? 'Stop' : 'Animate'}
              </button>
              <button type="button" onClick={() => loadNextPrediction()}>
                Next &gt;
              </button>
            </div>
          </div>
          <div className={classes.kml_links}>
            <div>
              <b>KML (For Google Earth)</b>
            </div>
            <div>
              <a href={KMLNetworkLinkURL}>Network link</a>
            </div>
            <div>
              <a href={KMLModelUrl} download={KMLModelFilename}>
                Most recent {selected_model_abbreviation} model run predictions.
              </a>
            </div>
            <div>
              <a href={KMLModelRunUrl} download={KMLModelRunFilename}>
                {selected_model_abbreviation}, model run {selected_model_run_timestamp} (UTC) predictions.
              </a>
            </div>
            <div>
              <a href={KMLUrl} download={KMLFilename}>
                {selected_model_abbreviation}, model run {selected_model_run_timestamp} (UTC) prediction{' '}
                {formatDatetimeInPST(selected_prediction_timestamp)} (PST)
              </a>
            </div>
            <div>
              <b>GeoJSON for GIS</b>
            </div>
            <div>
              <a href={geoJSONURI}>
                GeoJSON for {selected_model_abbreviation}, model run {selected_model_run_timestamp} (UTC) prediction{' '}
                {formatDatetimeInPST(selected_prediction_timestamp)} (PST)
              </a>
              <button type="button" onClick={handleCopyClick}>
                Copy GeoJSON link to clipboard
              </button>
            </div>
          </div>
        </div>
      </Container>
    </Root>
  )
}

export default React.memo(CHainesPage)
