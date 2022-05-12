import { TableCell } from '@mui/material'
import { StationDaily } from 'api/hfiCalculatorAPI'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { isNull, isUndefined } from 'lodash'
import React, { ReactElement } from 'react'

export interface RequiredDataCellProps {
  testId?: string
  classNameForRow?: string
  daily: StationDaily | undefined
  dailyKey: keyof StationDaily
  errorToolTipText: string
  decimalPlaces?: number
}

export const RequiredDataCell = ({
  testId,
  classNameForRow,
  daily,
  dailyKey,
  errorToolTipText,
  decimalPlaces = DECIMAL_PLACES
}: RequiredDataCellProps): ReactElement => {
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
        <TableCell className={classNameForRow}>{dataValue}</TableCell>
      )}
    </React.Fragment>
  )
}

export default React.memo(RequiredDataCell)
