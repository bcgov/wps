import { TableCell } from '@mui/material'
import { StationDaily } from 'api/hfiCalculatorAPI'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { UnSelectedTableCell } from 'features/hfiCalculator/components/StyledTableComponents'
import { isUndefined } from 'lodash'
import React from 'react'

export interface StatusCellProps {
  daily: StationDaily | undefined
  isRowSelected: boolean
}

const noForecastText = 'Forecast not available. Please check WFWX or contact a Forecaster.'
const noForecastElement = <div>{noForecastText}</div>

const observationValidCommentElement = (daily: StationDaily) => <div>{daily.observation_valid_comment}</div>

const StatusCell = (props: StatusCellProps) => {
  const TableCellComponent = props.isRowSelected ? TableCell : UnSelectedTableCell
  if (!props.isRowSelected) {
    return <TableCellComponent data-testid={'status-cell'} />
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
  return <TableCellComponent data-testid={'status-cell'}>{props.daily.status}</TableCellComponent>
}

export default React.memo(StatusCell)
