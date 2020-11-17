import React from 'react'
import { useSelector } from 'react-redux'

import { ErrorMessage, Button } from 'components'
import { Station } from 'api/stationAPI'
import {
  selectObservations,
  selectModels,
  selectModelSummaries,
  selectForecasts,
  selectWxDataLoading,
  selectForecastSummaries,
  selectHighResModels,
  selectHighResModelSummaries,
  selectRegionalModels,
  selectRegionalModelSummaries
} from 'app/rootReducer'

interface Props {
  onBtnClick: () => void
  selectedStations: Station[]
}

const GetWxDataButton = ({ onBtnClick, selectedStations }: Props) => {
  const { error: errFetchingObservations } = useSelector(selectObservations)
  const { error: errFetchingModels } = useSelector(selectModels)
  const { error: errFetchingModelSummaries } = useSelector(selectModelSummaries)
  const { error: errFetchingForecasts } = useSelector(selectForecasts)
  const { error: errFetchingForecastSummaries } = useSelector(selectForecastSummaries)
  const { error: errFetchingHighResModels } = useSelector(selectHighResModels)
  const { error: errFetchingHighResModelSummaries } = useSelector(
    selectHighResModelSummaries
  )
  const { error: errFetchingRegionalModels } = useSelector(selectRegionalModels)
  const { error: errFetchingRegionalModelSummaries } = useSelector(
    selectRegionalModelSummaries
  )
  const wxDataLoading = useSelector(selectWxDataLoading)
  const shouldBtnDisabled = selectedStations.length === 0

  return (
    <>
      <Button
        data-testid="get-wx-data-button"
        onClick={onBtnClick}
        disabled={shouldBtnDisabled}
        loading={wxDataLoading}
        variant="contained"
        color="primary"
      >
        Get Weather Data
      </Button>

      {errFetchingObservations && (
        <ErrorMessage
          error={errFetchingObservations}
          context="while fetching hourly observations"
          marginTop={5}
        />
      )}

      {errFetchingModels && (
        <ErrorMessage
          error={errFetchingModels}
          context="while fetching GDPS"
          marginTop={5}
        />
      )}

      {errFetchingModelSummaries && (
        <ErrorMessage
          error={errFetchingModelSummaries}
          context="while fetching GDPS summaries"
          marginTop={5}
        />
      )}

      {errFetchingForecasts && (
        <ErrorMessage
          error={errFetchingForecasts}
          context="while fetching noon forecasts"
          marginTop={5}
        />
      )}

      {errFetchingForecastSummaries && (
        <ErrorMessage
          error={errFetchingForecastSummaries}
          context="while fetching noon forecast summaries"
          marginTop={5}
        />
      )}

      {errFetchingHighResModels && (
        <ErrorMessage
          error={errFetchingHighResModels}
          context="while fetching HRDPS"
          marginTop={5}
        />
      )}

      {errFetchingHighResModelSummaries && (
        <ErrorMessage
          error={errFetchingHighResModelSummaries}
          context="while fetching HRDPS summaries"
          marginTop={5}
        />
      )}

      {errFetchingRegionalModels && (
        <ErrorMessage
          error={errFetchingRegionalModels}
          context="while fetching RDPS"
          marginTop={5}
        />
      )}

      {errFetchingRegionalModelSummaries && (
        <ErrorMessage
          error={errFetchingRegionalModelSummaries}
          context="while fetching RDPS summaries"
          marginTop={5}
        />
      )}
    </>
  )
}

export default React.memo(GetWxDataButton)
