import React from 'react'
import { useSelector } from 'react-redux'

import { ErrorMessage, Button } from 'components'
import { Station } from 'api/stationAPI'
import { selectReadings, selectModels } from 'app/rootReducer'

interface Props {
  onBtnClick: () => void
  selectedStations: Station[]
}

const GetWxDataButton = ({ onBtnClick, selectedStations }: Props) => {
  const { loading: loadingReadings, error: errorFetchingReadings } = useSelector(
    selectReadings
  )
  const { loading: loadingModels, error: errorFetchingModels } = useSelector(selectModels)

  const wxDataLoading = loadingModels || loadingReadings
  const isBtnDisabled = selectedStations.length === 0

  return (
    <>
      <Button
        data-testid="get-wx-data-button"
        onClick={onBtnClick}
        disabled={isBtnDisabled}
        loading={wxDataLoading}
        variant="contained"
        color="primary"
      >
        Get Historic Readings &amp; Global Model Data
      </Button>

      {errorFetchingModels && (
        <ErrorMessage
          error={errorFetchingModels}
          context="while fetching global model data"
          marginTop={5}
        />
      )}

      {errorFetchingReadings && (
        <ErrorMessage
          error={errorFetchingReadings}
          context="while fetching hourly readings"
          marginTop={5}
        />
      )}
    </>
  )
}

export default React.memo(GetWxDataButton)
