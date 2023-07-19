import { TableContainer, Table, TableRow, TableBody } from '@mui/material'
import { render } from '@testing-library/react'
import { StationDaily } from 'api/hfiCalculatorAPI'
import StatusCell from 'features/hfiCalculator/components/StatusCell'
import { ValidatedStationDaily } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'
import React from 'react'
describe('StatusCell', () => {
  const daily: StationDaily = {
    code: 1,
    status: 'ACTUAL',
    temperature: 1,
    relative_humidity: 1,
    wind_speed: 1,
    wind_direction: 1,
    grass_cure_percentage: 1,
    precipitation: 1,
    ffmc: 1,
    dmc: 1,
    dc: 1,
    isi: 1,
    bui: 1,
    fwi: 1,
    danger_class: 1,
    rate_of_spread: 1,
    hfi: 1,
    observation_valid: true,
    observation_valid_comment: '',
    intensity_group: 1,
    sixty_minute_fire_size: 1,
    fire_type: '',
    date: DateTime.fromObject({ year: 2021, month: 1, day: 1 }),
    last_updated: DateTime.fromObject({ year: 2021, month: 1, day: 1 })
  }
  const validDaily: ValidatedStationDaily = {
    daily: daily,
    valid: true
  }

  const invalidDaily: ValidatedStationDaily = {
    daily: { ...daily, observation_valid: false },
    valid: false
  }
  const renderStatusCell = (validatedDaily: ValidatedStationDaily | undefined, isRowSelected = true) => {
    return render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <StatusCell daily={validatedDaily?.daily} isRowSelected={isRowSelected} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  it('should render the status if it is defined', () => {
    const { getByTestId } = renderStatusCell(validDaily)
    expect(getByTestId('status-cell').innerHTML).toBe(validDaily.daily.status)
  })
  it('should not render the status or an error if it is defined but not selected', () => {
    const { getByTestId } = renderStatusCell(validDaily, false)
    expect(getByTestId('status-cell').innerHTML).toBe('')
  })
  it('should render error with tooltip if daily is undefined', () => {
    const { getByTestId } = renderStatusCell(undefined)
    expect(getByTestId('daily-status-no-forecast')).toBeDefined()
  })
  it('should render error with tooltip if daily is invalid', () => {
    const { getByTestId } = renderStatusCell(invalidDaily)
    expect(getByTestId('daily-status-obs-invalid')).toBeDefined()
  })
})
