import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { Box, IconButton, Tooltip, Typography } from '@mui/material'
import type { GridColumnHeaderParams } from '@mui/x-data-grid-pro'
import { weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { isEmpty, isNil } from 'lodash'
import { DateTime } from 'luxon'
import React from 'react'
import type { MoreCast2Row } from '@/features/moreCast2/interfaces'

interface ModelHeaderProps {
  params: Pick<GridColumnHeaderParams<MoreCast2Row>, 'field'> & {
    colDef: Pick<GridColumnHeaderParams<MoreCast2Row>['colDef'], 'field' | 'headerName'>
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
      <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <Typography style={{ fontSize: '14px', lineHeight: '20px' }}>{headerName}</Typography>
        <Tooltip
          data-testid={`${params.colDef.field}-model-run-tooltip`}
          title={`Model run: ${timestamp.toUTC().toFormat('MMM dd, yyyy HH:mm ZZZZ')}`}
          arrow
          placement="top"
        >
          <IconButton
            aria-label={`${headerName} model run information`}
            size="small"
            style={{ padding: '2px', height: '20px', width: '20px' }}
          >
            <InfoOutlinedIcon style={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>
      </Box>
    )
  }
  return (
    <Typography
      data-testid={`${params.colDef.field}-column-header`}
      style={{ fontSize: '14px', lineHeight: '20px', textAlign: 'center' }}
    >
      {headerName}
    </Typography>
  )
}

export default React.memo(ModelHeader)
