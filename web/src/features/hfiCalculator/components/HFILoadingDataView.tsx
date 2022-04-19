import {
  Table,
  TableBody,
  Container,
  CircularProgress,
  makeStyles
} from '@material-ui/core'
import { FireCentre } from 'api/hfiCalcAPI'
import {
  HFIResultResponse,
  PrepDateRange
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { isUndefined, isNull } from 'lodash'
import React from 'react'

export interface HFILoadingDataViewProps {
  loading: boolean
  stationDataLoading: boolean
  fireCentresLoading: boolean
  fireCentresError: string | null
  hfiError: string | null
  errorNotification: JSX.Element
  children: JSX.Element
  dateRange?: PrepDateRange
  selectedFireCentre?: FireCentre
  result?: HFIResultResponse
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
  errorNotification,
  children,
  dateRange,
  selectedFireCentre,
  result
}: HFILoadingDataViewProps) => {
  const classes = useStyles()

  const isLoading = () => {
    return loading || stationDataLoading || fireCentresLoading || isUndefined(result)
  }

  const isLoadingWithoutError = () =>
    isLoading() && isNull(fireCentresError) && isNull(hfiError)

  const isFireCentreUnselected = () =>
    (isUndefined(selectedFireCentre) || isUndefined(dateRange)) && !isLoading()
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
  return children
}

export default HFILoadingDataView
