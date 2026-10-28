import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material'
import type { WF1SkippedForecast } from '@wps/api/moreCast2API'
import { toBCPacificTime } from '@wps/utils/date'
import { DateTime } from 'luxon'

export interface ForecastPublishResult {
  savedCount: number
  publishedCount: number
  skipped: WF1SkippedForecast[]
}

interface Props {
  result: ForecastPublishResult | null
  onClose: () => void
}

const ForecastPublishResultDialog = ({ result, onClose }: Props) => (
  <Dialog
    open={result !== null}
    onClose={onClose}
    aria-labelledby="forecast-publish-result-title"
    fullWidth
    maxWidth="sm"
  >
    <DialogTitle id="forecast-publish-result-title">Forecasts saved</DialogTitle>
    {result && (
      <DialogContent>
        <DialogContentText>
          Saved {result.savedCount} {result.savedCount === 1 ? 'forecast' : 'forecasts'} in MoreCast. Published{' '}
          {result.publishedCount} to WF1.
        </DialogContentText>
        <DialogContentText sx={{ mt: 2 }}>
          WF1 already has actuals for the rows below. These forecasts were saved only in MoreCast.
        </DialogContentText>
        <Table aria-label="Forecasts saved only in MoreCast">
          <TableHead>
            <TableRow>
              <TableCell>Station</TableCell>
              <TableCell>Station code</TableCell>
              <TableCell>Forecast date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {result.skipped.map(row => (
              <TableRow key={`${row.station_code}-${row.for_date}`}>
                <TableCell>{row.station_name}</TableCell>
                <TableCell>{row.station_code}</TableCell>
                <TableCell>{toBCPacificTime(DateTime.fromMillis(row.for_date)).toISODate()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
    )}
    <DialogActions>
      <Button onClick={onClose}>Close</Button>
    </DialogActions>
  </Dialog>
)

export default ForecastPublishResultDialog
