import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import DayIndexHeaders from 'features/hfiCalculator/components/DayIndexHeaders'
import { range } from 'lodash'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import React from 'react'

describe('DayIndexHeaders', () => {
  it('should render day index headers for each day of the week', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <DayIndexHeaders />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )

    range(NUM_WEEK_DAYS).forEach(i => {
      expect(getByTestId(`ros-header-${i}`)).toBeDefined()
      expect(getByTestId(`hfi-header-${i}`)).toBeDefined()
      expect(getByTestId(`fig-header-${i}`)).toBeDefined()
      expect(getByTestId(`fire-starts-header-${i}`)).toBeDefined()
      expect(getByTestId(`prep-level-header-${i}`)).toBeDefined()
    })
  })
})
