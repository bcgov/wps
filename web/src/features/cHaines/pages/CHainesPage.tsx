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
  updateSelectedModelRun,
  updateSelectedPrediction,
  fetchCHainesGeoJSON,
} from 'features/cHaines/slices/cHainesModelRunsSlice'
import { Container, PageHeader, PageTitle } from 'components'
import { formatDateInPST } from 'utils/date'
import { logError } from 'utils/error'
import {
  getCHainesGeoJSONURI,
  getKMLNetworkLinkURI,
  getCHainesKMLURI,
  getCHainesKMLModelRunURI,
  getCHainesModelKMLURI,
} from 'api/cHainesAPI'

const useStyles = makeStyles({
  map: {
    height: '640px',
  },
  legend: {
    display: 'flex',
    backgroundColor: 'white',
  },
  description: {
    paddingLeft: 10,
    paddingRight: 10,
  },
  loading: {
    backgroundColor: 'white',
    opacity: 0.8,
    width: '100%',
  },
  label: {
    backgroundColor: 'white',
    opacity: 0.8,
  },
  extreme: {
    backgroundColor: '#ff0000',
    width: 30,
    height: 30,
  },
  high: {
    backgroundColor: '#FFA500',
    width: 30,
    height: 30,
  },
  moderate: {
    backgroundColor: '#ffff00',
    width: 30,
    height: 30,
  },
  controls: {
    display: 'flex',
  },
  kml_links: {
    marginLeft: '10px',
  },
  animateButton: {
    width: '70px',
  },
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
  // Set the default animation speed to 200ms.
  const [animationInterval, setAnimationInterval] = useState(200)
  const [selectedDatetime, setSelectedDateTime] = useState(() => {
    const d = new Date()
    const month = `${d.getMonth() + 1}`
    const date = `${d.getDate()}`
    const hours = `${d.getHours()}`
    const minutes = `${d.getMinutes()}`
    return `${d.getFullYear()}-${month.padStart(2, '0')}-${date.padStart(
      2,
      '0'
    )}T${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}`
  })
  const {
    model_runs,
    selected_model_run_timestamp,
    model_run_predictions,
    selected_prediction_timestamp,
    selected_model_abbreviation,
  } = useSelector(selectCHainesModelRuns)

  const loadModelPrediction = (
    model_abbreviation: string,
    model_run_timestamp: string,
    prediction_timestamp: string
  ) => {
    dispatch(updateSelectedPrediction(prediction_timestamp))
    if (isLoaded(model_abbreviation, model_run_timestamp, prediction_timestamp)) {
      showLayer(model_abbreviation, model_run_timestamp, prediction_timestamp)
      // if it's already loaded, we can just show it
    } else {
      // fetch the data
      dispatch(
        fetchCHainesGeoJSON(model_abbreviation, model_run_timestamp, prediction_timestamp)
      )
    }
  }

  const isLoaded = (
    model_abbreviation: string,
    model_run_timestamp: string,
    prediction_timestamp: string
  ) => {
    return (
      model_abbreviation in model_run_predictions &&
      model_run_timestamp in model_run_predictions[model_abbreviation] &&
      prediction_timestamp in
        model_run_predictions[model_abbreviation][model_run_timestamp]
    )
  }

  useEffect(() => {
    dispatch(fetchModelRuns(selectedDatetime))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (
      selected_prediction_timestamp &&
      selected_model_run_timestamp &&
      model_runs.length > 0
    ) {
      loadModelPrediction(
        selected_model_abbreviation,
        selected_model_run_timestamp,
        selected_prediction_timestamp
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model_runs])

  useEffect(() => {
    if (selected_model_abbreviation in model_run_predictions) {
      if (
        selected_model_run_timestamp in model_run_predictions[selected_model_abbreviation]
      ) {
        if (
          selected_prediction_timestamp in
          model_run_predictions[selected_model_abbreviation][selected_model_run_timestamp]
        ) {
          showLayer(
            selected_model_abbreviation,
            selected_model_run_timestamp,
            selected_prediction_timestamp
          )
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model_run_predictions])

  useEffect(() => {
    mapRef.current = L.map('map-with-selectable-wx-stations', {
      center: [55, -123.6],
      zoom: 5,
      // scrollWheelZoom: false,
      zoomAnimation: true,
      // layers: [topoLayer, stationOverlay]
    })
    L.control.scale().addTo(mapRef.current)

    const baseLayer = tiledMapLayer({
      //url:  'https://maps.gov.bc.ca/arcserver/rest/services/province/web_mercator_cache/MapServer'
      url: 'https://maps.gov.bc.ca/arcserver/rest/services/Province/roads_wm/MapServer',
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
          maxZoom: 18,
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
          maxZoom: 18,
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
          maxZoom: 18,
        }
      )
      .addTo(mapRef.current)

    // Create and add the legend.
    const customControl = L.Control.extend({
      onAdd: function () {
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

      onRemove: function () {
        //
      },
    })
    new customControl({ position: 'bottomleft' }).addTo(mapRef.current)

    // Destroy the map and clear all related event listeners when the component unmounts
    return () => {
      mapRef.current?.remove()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Initialize the map only once

  const predictionIsLoadedCheck = isLoaded(
    selected_model_abbreviation,
    selected_model_run_timestamp,
    selected_prediction_timestamp
  )
  useEffect(() => {
    if (mapRef.current && selected_model_run_timestamp && selected_prediction_timestamp) {
      if (
        isLoaded(
          selected_model_abbreviation,
          selected_model_run_timestamp,
          selected_prediction_timestamp
        )
      ) {
        const customControl = L.Control.extend({
          onAdd: function () {
            const html = (
              <div className={classes.label}>
                <div>
                  {selected_model_abbreviation} model run: {selected_model_run_timestamp}{' '}
                  (UTC)
                </div>
                <div>
                  {selected_model_abbreviation} prediction:{' '}
                  {formatDateInPST(selected_prediction_timestamp)} (PST)
                </div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: function () {
            //
          },
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
          onAdd: function () {
            const html = (
              <div className={classes.loading}>
                <div>LOADING: {selected_prediction_timestamp} (UTC)</div>
              </div>
            )

            const div = L.DomUtil.create('div')
            div.innerHTML = ReactDOMServer.renderToString(html)
            return div
          },

          onRemove: function () {
            //
          },
        })
        if (loadingLayerRef.current) {
          mapRef.current.removeControl(loadingLayerRef.current)
        }
        loadingLayerRef.current = new customControl({ position: 'topright' })
        loadingLayerRef.current.addTo(mapRef.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selected_model_run_timestamp,
    selected_prediction_timestamp,
    model_run_predictions,
    predictionIsLoadedCheck,
    isAnimating,
  ])

  const createLayer = (data: FeatureCollection) => {
    const defaults = {
      fillOpacity: 0.5,
      weight: 2,
    }
    return L.geoJSON(data, {
      style: (feature) => {
        switch (feature?.properties.c_haines_index) {
          case '4-8':
            // yellow
            return {
              ...defaults,
              color: '#ffff00',
            }
          case '8-11':
            return {
              ...defaults,
              color: '#FFA500',
            }
          case '>11':
            // red
            return {
              ...defaults,
              color: '#ff0000',
            }
          default:
            return {}
        }
      },
    })
  }

  const getLayer = (
    model: string,
    model_timestamp: string,
    prediction_timestamp: string
  ) => {
    const layerKey = `${model}-${model_timestamp}-${prediction_timestamp}`
    if (layerKey in layersRef.current) {
      return layersRef.current[layerKey]
    } else {
      const data = model_run_predictions[model][model_timestamp][prediction_timestamp]
      const geoJsonLayer = createLayer(data)
      layersRef.current[layerKey] = geoJsonLayer
      return geoJsonLayer
    }
  }

  const showLayer = (
    model: string,
    model_run_timestamp: string,
    prediction_timestamp: string
  ) => {
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
      // For some reason, the API sometimes returns geosjon data with no features (maybe they're in the
      // process of being inserted?)
      logError(exception)
    }
  }

  const handleChangeDateTime = (
    event: React.ChangeEvent<{ name?: string; value: string }>
  ) => {
    setSelectedDateTime(event.target.value)
    dispatch(fetchModelRuns(event.target.value))
  }

  const handleChangeModel = (
    event: React.ChangeEvent<{ name?: string; value: string }>
  ) => {
    dispatch(updateSelectedModel(event.target.value))
    stopAnimation()
    // If the model has been changed, we need to load a different prediction.
    const model_run = model_runs.find(
      (instance) => instance.model.abbrev === event.target.value
    )
    if (model_run) {
      if (model_run.prediction_timestamps.length > 0) {
        loadModelPrediction(
          event.target.value,
          model_run.model_run_timestamp,
          model_run.prediction_timestamps[0]
        )
      }
    }
  }

  const handleChangeModelRun = (
    event: React.ChangeEvent<{ name?: string; value: string }>
  ) => {
    dispatch(updateSelectedModelRun(event.target.value))
    stopAnimation()
    // If the model run has been changed, we also have to load a different prediction.
    const model_run = model_runs.find(
      (instance) =>
        instance.model_run_timestamp === event.target.value &&
        instance.model.abbrev === selected_model_abbreviation
    )
    if (model_run) {
      if (model_run.prediction_timestamps.length > 0) {
        loadModelPrediction(
          selected_model_abbreviation,
          event.target.value,
          model_run.prediction_timestamps[0]
        )
      }
    }
  }

  const handlePredictionChange = (
    event: React.ChangeEvent<{ name?: string; value: string }>
  ) => {
    stopAnimation()
    loadModelPrediction(
      selected_model_abbreviation,
      selected_model_run_timestamp,
      event.target.value
    )
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

  const handleIntervalChange = (
    event: React.ChangeEvent<{ name?: string; value: string }>
  ) => {
    setAnimationInterval(Number(event.target.value))
  }

  const loadNextPrediction = () => {
    const model_run = model_runs.find(
      (instance) =>
        instance.model_run_timestamp === selected_model_run_timestamp &&
        instance.model.abbrev === selected_model_abbreviation
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.findIndex(
        (value) => value === selected_prediction_timestamp
      )
      const nextIndex = index + 1 < model_run.prediction_timestamps.length ? index + 1 : 0
      loadModelPrediction(
        selected_model_abbreviation,
        selected_model_run_timestamp,
        model_run.prediction_timestamps[nextIndex]
      )
    }
  }

  const loadPreviousPrediction = () => {
    const model_run = model_runs.find(
      (instance) =>
        instance.model_run_timestamp === selected_model_run_timestamp &&
        instance.model.abbrev === selected_model_abbreviation
    )
    if (model_run) {
      const index = model_run.prediction_timestamps.findIndex(
        (value) => value === selected_prediction_timestamp
      )
      const nextIndex = index > 0 ? index - 1 : model_run.prediction_timestamps.length - 1
      loadModelPrediction(
        selected_model_abbreviation,
        selected_model_run_timestamp,
        model_run.prediction_timestamps[nextIndex]
      )
    }
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

  const KMLModelRunUrl = getCHainesKMLModelRunURI(
    selected_model_abbreviation,
    selected_model_run_timestamp
  )

  const KMLModelFilename = `${selected_model_abbreviation}.kml`

  const KMLModelRunFilename = `${selected_model_abbreviation}-${encodeURIComponent(
    selected_model_run_timestamp
  )}.kml`

  const KMLFilename = `${selected_model_abbreviation}-${encodeURIComponent(
    selected_model_run_timestamp
  )}-${encodeURIComponent(selected_prediction_timestamp)}.kml`

  return (
    <main>
      <PageHeader title="Predictive Services Unit" productName="C-Haines" />
      <PageTitle title="C-Haines - Alpha (Experimental)" />
      <Container maxWidth="xl">
        <div id="map-with-selectable-wx-stations" className={classes.map} />
        <div className={classes.controls}>
          <div>
            <div>
              Date of interest:
              <input
                type="datetime-local"
                value={selectedDatetime}
                onChange={handleChangeDateTime}
              ></input>
            </div>
            <div>
              Model:
              <input
                type="radio"
                value="GDPS"
                checked={selected_model_abbreviation === 'GDPS'}
                onChange={handleChangeModel}
              />
              <label>GDPS</label>
              <input
                type="radio"
                value="RDPS"
                checked={selected_model_abbreviation === 'RDPS'}
                onChange={handleChangeModel}
              />
              <label>RDPS</label>
              <input
                type="radio"
                value="HRDPS"
                checked={selected_model_abbreviation === 'HRDPS'}
                onChange={handleChangeModel}
              />
              <label>HRDPS</label>
            </div>
            <div>
              Model runs:
              {model_runs
                .filter((model_run) => {
                  return model_run.model.abbrev === selected_model_abbreviation
                })
                .map((model_run, i) => (
                  <div key={i}>
                    <input
                      type="radio"
                      value={model_run.model_run_timestamp}
                      checked={
                        model_run.model_run_timestamp === selected_model_run_timestamp
                      }
                      onChange={handleChangeModelRun}
                    />
                    <label>
                      {model_run.model.abbrev} {model_run.model_run_timestamp} (UTC)
                    </label>
                  </div>
                ))}
            </div>
            <div>
              Predictions:
              <select
                value={selected_prediction_timestamp}
                onChange={handlePredictionChange}
              >
                {model_runs
                  .filter((model_run) => {
                    return (
                      model_run.model_run_timestamp === selected_model_run_timestamp &&
                      model_run.model.abbrev === selected_model_abbreviation
                    )
                  })
                  .map((model_run, i) =>
                    model_run.prediction_timestamps.map((prediction_timestamp, i2) => (
                      <option key={`${i}-${i2}`} value={prediction_timestamp}>
                        {formatDateInPST(prediction_timestamp)} (PST)
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
              <button onClick={() => loadPreviousPrediction()}>&lt; Prev</button>
              <button onClick={() => toggleAnimate()} className={classes.animateButton}>
                {isAnimating ? 'Stop' : 'Animate'}
              </button>
              <button onClick={() => loadNextPrediction()}>Next &gt;</button>
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
                {selected_model_abbreviation}, model run {selected_model_run_timestamp}{' '}
                (UTC) predictions.
              </a>
            </div>
            <div>
              <a href={KMLUrl} download={KMLFilename}>
                {selected_model_abbreviation}, model run {selected_model_run_timestamp}{' '}
                (UTC) prediction {formatDateInPST(selected_prediction_timestamp)} (PST)
              </a>
            </div>
            <div>
              <b>GeoJSON for GIS</b>
            </div>
            <div>
              <a href={geoJSONURI}>
                GeoJSON for {selected_model_abbreviation}, model run{' '}
                {selected_model_run_timestamp} (UTC) prediction{' '}
                {formatDateInPST(selected_prediction_timestamp)} (PST)
              </a>
              <button onClick={handleCopyClick}>Copy GeoJSON link to clipboard</button>
            </div>
          </div>
        </div>
      </Container>
    </main>
  )
}

export default React.memo(CHainesPage)
