import { getDetailedStations, StationSource } from '@wps/api/stationAPI'
import { selectFireWeatherStations } from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import { AccuracyWeatherVariableEnum } from 'features/fireWeather/components/AccuracyVariablePicker'
import {
  computeRHAccuracyColor,
  computeRHAccuracySize,
  computeStroke,
  computeTempAccuracyColor,
  computeTempAccuracySize
} from 'features/fireWeather/components/maps/stationAccuracy'
import VectorLayer from 'features/map/VectorLayer'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import GeoJSON from 'ol/format/GeoJSON'
import * as olSource from 'ol/source'
import { Fill, Style } from 'ol/style'
import CircleStyle from 'ol/style/Circle'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

interface Props {
  toiFromQuery: string
  selectedWxVariable: AccuracyWeatherVariableEnum
}
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
  }, [dispatch])

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
