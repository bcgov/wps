import React from 'react'
import { Box, IconButton, Tooltip, Typography } from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'
import { DateTime } from 'luxon'
import { MoreCast2Row } from '@/features/moreCast2/interfaces'
import { GridColumnHeaderParams } from '@mui/x-data-grid-pro'
import { weatherModelsWithTooltips } from '@/api/moreCast2API'
import { isEmpty, isNil } from 'lodash'

interface ModelHeaderProps {
  params: Pick<GridColumnHeaderParams, 'field'> & {
    colDef: Pick<GridColumnHeaderParams['colDef'], 'field' | 'headerName'>
  }
  allRows?: MoreCast2Row[]
}

const ModelHeader = ({ params, allRows }: ModelHeaderProps) => {
  const headerName = params.colDef.headerName ?? ''
  const modelType = weatherModelsWithTooltips.find(model => headerName === model)
  const timestampField = `predictionRunTimestamp${modelType}` as keyof MoreCast2Row

  const latestTimestamp = () => {
    if (isNil(allRows) || isEmpty(allRows)) {
      return null
    }
    const timestamps = allRows
      .map(row => DateTime.fromISO(row[timestampField] as string))
      .filter(timestamp => timestamp.isValid)
      .toSorted((timeA, timeB) => timeA.toMillis() - timeB.toMillis())

    return timestamps.length > 0 ? timestamps[timestamps.length - 1] : null
  }
  const timestamp = latestTimestamp()

  if (modelType && allRows && allRows.length > 0 && timestamp) {
    return (
      <Box style={{ display: 'flex', alignItems: 'center' }}>
        <Tooltip
          data-testid={`${params.colDef.field}-model-run-tooltip`}
          title={`Model run: ${timestamp.toUTC().toFormat('MMM dd, yyyy HH:mm ZZZZ')}`}
          arrow
          placement="top"
        >
          <Box style={{ display: 'flex', alignItems: 'center' }}>
            <Typography style={{ fontSize: '14px' }}>{headerName}</Typography>
            <IconButton size="small" style={{ padding: '2px' }}>
              <InfoIcon style={{ fontSize: '12px' }} />
            </IconButton>
          </Box>
        </Tooltip>
      </Box>
    )
  }
  return (
    <Typography data-testid={`${params.colDef.field}-column-header`} style={{ fontSize: '14px' }}>
      {headerName}
    </Typography>
  )
}

export default React.memo(ModelHeader)
