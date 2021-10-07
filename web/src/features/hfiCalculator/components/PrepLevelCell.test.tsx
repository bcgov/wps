import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import React from 'react'

const prepLevelTest = (MIG: number, expectedPrep: string, expectedClass: any) => {
  const { getByTestId, getByText } = render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <PrepLevelCell
              testid={'weekly-prep-level-afton'}
              areaName={'afton'}
              meanIntensityGroup={MIG}
            ></PrepLevelCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )

  const cell = getByTestId('weekly-prep-level-afton')
  expect(cell.className).toMatch(expectedClass)
  expect(getByText(expectedPrep)).toBeDefined
}

describe('PrepLevelCell', () => {
  it('should return a cell with a classname of prepLevel1 and a text prep level of 1', () => {
    prepLevelTest(1, '1', /makeStyles-prepLevel1-/)
  })
  it('should return a cell with a classname of prepLevel1 and a text prep level of 1', () => {
    prepLevelTest(2, '1', /makeStyles-prepLevel1-/)
  })
  it('should return a cell with a classname of prepLevel2 and a text prep level of 2', () => {
    prepLevelTest(3, '2', /makeStyles-prepLevel2-/)
  })
  it('should return a cell with a classname of prepLevel3 and a text prep level of 3', () => {
    prepLevelTest(4, '3', /makeStyles-prepLevel3-/)
  })
  it('should return a cell with a classname of prepLevel4 and a text prep level of 4', () => {
    prepLevelTest(5, '4', /makeStyles-prepLevel4-/)
  })
  it('should return a cell with a classname of prepLevel4 and a text prep level of 4', () => {
    prepLevelTest(6, '4', /makeStyles-prepLevel4-/)
  })
})
