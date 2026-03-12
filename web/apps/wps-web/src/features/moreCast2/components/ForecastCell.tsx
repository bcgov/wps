import { Grid, Tooltip } from '@mui/material'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle'
import AddBoxIcon from '@mui/icons-material/AddBox'
import { MEDIUM_GREY } from 'app/theme'
import ValidatedForecastCell from '@/features/moreCast2/components/ValidatedForecastCell'

interface ForecastCellProps {
  disabled: boolean
  label: string
  showGreaterThan: boolean
  showLessThan: boolean
  value: Pick<GridRenderCellParams, 'formattedValue'>
  validator?: (value: string) => string
}

const ForecastCell = ({ disabled, label, showGreaterThan, showLessThan, value, validator }: ForecastCellProps) => {
  // We should never display both less than and greater than icons at the same time
  if (showGreaterThan && showLessThan) {
    throw Error('ForecastCell cannot show both greater than and less than icons at the same time.')
  }

  return (
    <Grid container sx={{ justifyContent: 'center', alignItems: 'center' }}>
      <Grid item xs={2}>
        {showLessThan && (
          <Tooltip placement="bottom-end" title="Lower than actual">
            <RemoveCircleIcon
              data-testid="forecast-cell-less-than-icon"
              sx={{ color: MEDIUM_GREY, fontSize: '1.15rem' }}
            />
          </Tooltip>
        )}
      </Grid>
      <Grid item xs={8}>
        <ValidatedForecastCell disabled={disabled} label={label} value={value} validator={validator} />
      </Grid>
      <Grid item xs={2} sx={{ marginLeft: 'auto' }}>
        {showGreaterThan && (
          <Tooltip placement="bottom-start" title="Higher than actual">
            <AddBoxIcon
              data-testid="forecast-cell-greater-than-icon"
              sx={{ color: MEDIUM_GREY, fontSize: '1.25rem', marginLeft: '2px' }}
            />
          </Tooltip>
        )}
      </Grid>
    </Grid>
  )
}

export default ForecastCell
