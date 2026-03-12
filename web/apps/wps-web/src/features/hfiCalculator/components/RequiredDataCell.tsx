import { TableCell } from '@mui/material'
import { StationDaily } from 'api/hfiCalculatorAPI'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { UnSelectedTableCell } from 'features/hfiCalculator/components/StyledTableComponents'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { isNull, isUndefined } from 'lodash'
import React, { ReactElement } from 'react'

export interface RequiredDataCellProps {
  testId?: string
  isRowSelected: boolean
  classNameForRow?: string
  daily: StationDaily | undefined
  dailyKey: keyof StationDaily
  errorToolTipText: string
  decimalPlaces?: number
}

export const RequiredDataCell = ({
  testId,
  isRowSelected,
  daily,
  dailyKey,
  errorToolTipText,
  decimalPlaces = DECIMAL_PLACES
}: RequiredDataCellProps): ReactElement => {
  const TableCellComponent = isRowSelected ? TableCell : UnSelectedTableCell

  const dataValue = daily ? Number(daily[dailyKey])?.toFixed(decimalPlaces) : ''

  return (
    <React.Fragment>
      {(daily && isUndefined(daily[dailyKey])) || (daily && isNull(daily[dailyKey])) ? (
        <TableCell data-testid={testId}>
          <ErrorIconWithTooltip
            isDataCell={true}
            tooltipElement={<div>{errorToolTipText}</div>}
            tooltipAriaText={[errorToolTipText]}
          />
        </TableCell>
      ) : (
        <TableCellComponent>{dataValue}</TableCellComponent>
      )}
    </React.Fragment>
  )
}

export default React.memo(RequiredDataCell)
