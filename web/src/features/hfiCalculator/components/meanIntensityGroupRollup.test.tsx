import { TableContainer, Table, TableRow, TableBody } from '@material-ui/core'
import { render } from '@testing-library/react'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import { PlanningArea } from 'api/hfiCalcAPI'
import React from 'react'
describe('Mean Intensity Group Rollup', () => {
  const planningArea: PlanningArea = {
    id: 1,
    name: 'Test Area',
    stations: [],
    order_of_appearance_in_list: 0
  }

  it('should return nothing in cell when dailies are empty', () => {
    const { getByTestId, queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <MeanIntensityGroupRollup
                area={planningArea}
                dailies={[]}
                meanIntensityGroup={undefined}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('zone-Test Area-mig-error').length === 0)
    expect(getByTestId('zone-1-mean-intensity')).toBeDefined()
  })
})
