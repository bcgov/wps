import { Table, TableBody } from '@mui/material'
import { FireCentre } from 'api/hfiCalculatorAPI'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { isUndefined, isNull } from 'lodash'
import React from 'react'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import LoadingBackdrop from 'features/hfiCalculator/components/LoadingBackdrop'

export interface HFILoadingDataContainerProps {
  pdfLoading: boolean
  fuelTypesLoading: boolean
  stationDataLoading: boolean
  fireCentresLoading: boolean
  stationsUpdateLoading: boolean
  fireCentresError: string | null
  hfiError: string | null
  children: JSX.Element
  dateRange?: PrepDateRange
  selectedFireCentre?: FireCentre
}

const HFILoadingDataContainer = ({
  pdfLoading,
  fuelTypesLoading,
  stationDataLoading,
  fireCentresLoading,
  fireCentresError,
  stationsUpdateLoading,
  hfiError,
  children,
  dateRange,
  selectedFireCentre
}: HFILoadingDataContainerProps) => {
  const buildErrorNotification = () => {
    if (!isNull(fireCentresError) || !isNull(hfiError)) {
      return <HFIErrorAlert errors={[hfiError, fireCentresError]} />
    }
    return <React.Fragment></React.Fragment>
  }

  const isLoading = () => {
    return pdfLoading || fuelTypesLoading || stationDataLoading || fireCentresLoading || stationsUpdateLoading
  }

  const isLoadingWithoutError = () => isLoading() && isNull(fireCentresError) && isNull(hfiError)

  const isFireCentreUnselected = () => (isUndefined(selectedFireCentre) || isUndefined(dateRange)) && !isLoading()

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
  }

  return (
    <React.Fragment>
      {errorNotification}
      {children}
      <LoadingBackdrop isLoadingWithoutError={isLoadingWithoutError()} />
    </React.Fragment>
  )
}

export default React.memo(HFILoadingDataContainer)
