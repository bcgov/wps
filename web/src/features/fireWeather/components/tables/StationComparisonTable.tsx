import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Table from '@material-ui/core/Table'
import TableBody from '@material-ui/core/TableBody'
import TableCell from '@material-ui/core/TableCell'
import TableContainer from '@material-ui/core/TableContainer'
import TableRow from '@material-ui/core/TableRow'
import TableHead from '@material-ui/core/TableHead'
// import TableSortLabel from '@material-ui/core/TableSortLabel'
import { GeoJsonStation } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { getNoonDate, formatDateInPST, reformatDate } from 'utils/date'
import {
  PRECIP_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'

const useStyles = makeStyles({
  tableContainer: {}
})

interface Props {
  timeOfInterest: string
  stationCodes: number[]
  stationsByCode: Record<number, GeoJsonStation | undefined>
  allNoonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
  observationsByStation: Record<number, ObservedValue[] | undefined>
  allHighResModelsByStation: Record<number, ModelValue[] | undefined>
  allRegionalModelsByStation: Record<number, ModelValue[] | undefined>
  noonModelsByStation: Record<number, ModelValue[] | undefined>
}

const findNoonMatch = (
  noonDate: string,
  collection: ModelValue[] | undefined
): ModelValue | undefined => {
  return collection?.find((item: ModelValue) => reformatDate(item.datetime) === noonDate)
}

const StationComparisonTable = (props: Props) => {
  const classes = useStyles()
  const noonDate = getNoonDate(props.timeOfInterest)
  return (
    <div>
      <div>Station comparison for {formatDateInPST(noonDate)} PDT</div>
      <TableContainer className={classes.tableContainer}>
        <Table stickyHeader size="small" aria-label="sortable wx table">
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              <TableCell colSpan={5}>Temperature</TableCell>
              <TableCell>Relative Humidity</TableCell>
              <TableCell>Wind Speed + Direction</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Weather Stations</TableCell>
              <TableCell>Observed</TableCell>
              <TableCell>Forecast</TableCell>
              <TableCell>HRDPS</TableCell>
              <TableCell>RDPS</TableCell>
              <TableCell>GDPS</TableCell>
              <TableCell></TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {props.stationCodes.map((stationCode: number, idx: number) => {
              const station = props.stationsByCode[stationCode]
              const noonForecasts = props.allNoonForecastsByStation[stationCode]
              const noonForecast = noonForecasts?.find(
                forecast => reformatDate(forecast.datetime) === noonDate
              )
              const observations = props.observationsByStation[stationCode]
              const observation = observations?.find(
                observation => reformatDate(observation.datetime) == noonDate
              )
              const hrdpsModelPrediction = findNoonMatch(
                noonDate,
                props.allHighResModelsByStation[stationCode]
              )
              const rdpsModelPrediction = findNoonMatch(
                noonDate,
                props.allRegionalModelsByStation[stationCode]
              )
              const gdpsModelPrediction = findNoonMatch(
                noonDate,
                props.noonModelsByStation[stationCode]
              )
              return (
                <TableRow key={idx}>
                  <TableCell>
                    {station?.properties.name} ({stationCode})
                  </TableCell>
                  <TableCell>{observation?.temperature}</TableCell>
                  <TableCell>{noonForecast?.temperature}</TableCell>
                  <TableCell>
                    {hrdpsModelPrediction?.temperature?.toFixed(
                      TEMPERATURE_VALUES_DECIMAL
                    )}
                  </TableCell>
                  <TableCell>
                    {rdpsModelPrediction?.temperature?.toFixed(
                      TEMPERATURE_VALUES_DECIMAL
                    )}
                  </TableCell>
                  <TableCell>
                    {gdpsModelPrediction?.temperature?.toFixed(
                      TEMPERATURE_VALUES_DECIMAL
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  )
}

export default React.memo(StationComparisonTable)
