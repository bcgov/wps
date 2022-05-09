import { TableContainer, Table, TableRow, TableBody } from '@mui/material'
import { render } from '@testing-library/react'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import React from 'react'
describe('Mean Intensity Group Rollup', () => {
  const planningArea: PlanningArea = {
    id: 1,
    name: 'Test Area',
    stations: [],
    order_of_appearance_in_list: 0
  }

  it('should show error icon in cell when dailies are empty', () => {
    const { queryAllByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <MeanIntensityGroupRollup
                area={planningArea}
                dailies={[]}
                meanIntensityGroup={undefined}
                fuelTypes={[]}
                planningAreaStationInfo={{}}
              />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(queryAllByTestId('zone-Test Area-mig-error').length > 0)
  })
})
