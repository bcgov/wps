import { TableContainer, Table, TableRow, TableBody } from '@material-ui/core'
import { render } from '@testing-library/react'
import StatusCell from 'features/hfiCalculator/components/StatusCell'
import { ValidatedStationDaily } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'
import React from 'react'
describe('StatusCell', () => {
  const validDaily: ValidatedStationDaily = {
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
    valid: true
  }

  const invalidDaily: ValidatedStationDaily = {
    ...validDaily,
    observation_valid: false,
    valid: false
  }
  const renderStatusCell = (daily: ValidatedStationDaily | undefined) => {
    return render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <StatusCell daily={daily} className={''} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  it('should render the status if it is defined', () => {
    const { getByTestId } = renderStatusCell(validDaily)
    expect(getByTestId('status-cell').innerHTML).toBe(validDaily.status)
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
