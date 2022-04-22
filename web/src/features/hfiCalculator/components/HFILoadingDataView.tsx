import { Table, TableBody, Container, CircularProgress } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FireCentre } from 'api/hfiCalcAPI'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { isUndefined, isNull } from 'lodash'
import React from 'react'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'

export interface HFILoadingDataViewProps {
  loading: boolean
  stationDataLoading: boolean
  fireCentresLoading: boolean
  fireCentresError: string | null
  hfiError: string | null
  children: JSX.Element
  dateRange?: PrepDateRange
  selectedFireCentre?: FireCentre
}

const useStyles = makeStyles(() => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  }
}))
const HFILoadingDataView = ({
  loading,
  stationDataLoading,
  fireCentresLoading,
  fireCentresError,
  hfiError,
  children,
  dateRange,
  selectedFireCentre
}: HFILoadingDataViewProps) => {
  const classes = useStyles()

  const buildErrorNotification = () => {
    if (!isNull(fireCentresError) || !isNull(hfiError)) {
      return (
        <HFIErrorAlert hfiDailiesError={hfiError} fireCentresError={fireCentresError} />
      )
    }
    return <React.Fragment></React.Fragment>
  }

  const isLoading = () => {
    return loading || stationDataLoading || fireCentresLoading
  }

  const isLoadingWithoutError = () =>
    isLoading() && isNull(fireCentresError) && isNull(hfiError)

  const isFireCentreUnselected = () =>
    (isUndefined(selectedFireCentre) || isUndefined(dateRange)) && !isLoading()

  const errorNotification = buildErrorNotification()

  if (isFireCentreUnselected()) {
    return (
      <React.Fragment>
        {errorNotification}
        <Table>
          <TableBody>
            <EmptyFireCentreRow />
          </TableBody>
        </Table>
      </React.Fragment>
    )
  } else if (isLoadingWithoutError()) {
    return (
      <Container className={classes.container} data-testid="loading-container">
        {errorNotification}
        <CircularProgress />
      </Container>
    )
  }

  return (
    <React.Fragment>
      {errorNotification}
      {children}
    </React.Fragment>
  )
}

export default HFILoadingDataView
