import { TableCell } from '@mui/material'
import { StationDaily } from 'api/hfiCalculatorAPI'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { isUndefined } from 'lodash'
import React from 'react'

export interface StatusCellProps {
  daily: StationDaily | undefined
  className: string | undefined
  isRowSelected: boolean
}

const noForecastText = 'Forecast not available. Please check WFWX or contact a Forecaster.'
const noForecastElement = <div>{noForecastText}</div>

const observationValidCommentElement = (daily: StationDaily) => <div>{daily.observation_valid_comment}</div>

const StatusCell = (props: StatusCellProps) => {
  if (!props.isRowSelected) {
    return <TableCell data-testid={'status-cell'} className={props.className} />
  }
  if (isUndefined(props.daily)) {
    return (
      <TableCell data-testid={'status-cell'}>
        <ErrorIconWithTooltip
          testId="daily-status-no-forecast"
          isDataCell={true}
          tooltipElement={noForecastElement}
          tooltipAriaText={[noForecastText]}
        />
      </TableCell>
    )
  }
  if (props.daily.observation_valid === false) {
    return (
      <TableCell data-testid={'status-cell'}>
        <ErrorIconWithTooltip
          testId="daily-status-obs-invalid"
          isDataCell={true}
          tooltipElement={observationValidCommentElement(props.daily)}
          tooltipAriaText={[props.daily.observation_valid_comment]}
        />
      </TableCell>
    )
  }
  return (
    <TableCell data-testid={'status-cell'} className={props.className}>
      {props.daily.status}
    </TableCell>
  )
}

export default React.memo(StatusCell)
