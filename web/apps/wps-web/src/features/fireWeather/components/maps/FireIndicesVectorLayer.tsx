import React, { useEffect } from 'react'
import * as olSource from 'ol/source'
import GeoJSON from 'ol/format/GeoJSON'
import { getDetailedStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import VectorLayer from 'features/map/VectorLayer'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { useDispatch, useSelector } from 'react-redux'
import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import {
  computeRHAccuracyColor,
  computeRHAccuracySize,
  computeStroke,
  computeTempAccuracyColor,
  computeTempAccuracySize
} from 'features/fireWeather/components/maps/stationAccuracy'
import { Style, Fill } from 'ol/style'
import CircleStyle from 'ol/style/Circle'
import { AppDispatch } from 'app/store'

interface Props {
  toiFromQuery: string
  selectedWxVariable: AccuracyWeatherVariableEnum
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const rhPointStyleFunction = (feature: any) => {
  const rhPointColor = computeRHAccuracyColor(feature.values_)
  return new Style({
    image: new CircleStyle({
      radius: computeRHAccuracySize(feature.values_),
      fill: new Fill({ color: rhPointColor }),
      stroke: computeStroke(rhPointColor)
    })
  })
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const tempPointStyleFunction = (feature: any) => {
  const tempPointColor = computeTempAccuracyColor(feature.values_)
  return new Style({
    image: new CircleStyle({
      radius: computeTempAccuracySize(feature.values_),
      fill: new Fill({ color: tempPointColor }),
      stroke: computeStroke(tempPointColor)
    })
  })
}

const FireIndicesVectorLayer = ({ toiFromQuery, selectedWxVariable }: Props) => {
  const dispatch: AppDispatch = useDispatch()
  const { stations } = useSelector(selectFireWeatherStations)

  const styleFunction =
    selectedWxVariable === AccuracyWeatherVariableEnum['Relative Humidity']
      ? rhPointStyleFunction
      : tempPointStyleFunction

  useEffect(() => {
    dispatch(fetchWxStations(getDetailedStations, StationSource.unspecified, toiFromQuery))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <VectorLayer
      source={
        new olSource.Vector({
          features: new GeoJSON().readFeatures(
            { type: 'FeatureCollection', features: stations },
            {
              featureProjection: 'EPSG:3857'
            }
          )
        })
      }
      style={styleFunction}
      zIndex={1}
    />
  )
}

export default React.memo(FireIndicesVectorLayer)
