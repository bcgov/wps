import { Table, TableBody, TableContainer, TableRow } from '@material-ui/core'
import { render } from '@testing-library/react'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import React from 'react'
describe('PrepLevelCell', () => {
  it('should return a cell with a classname of prepLevel1 and a text prep level of 1', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <PrepLevelCell areaName={'afton'} meanIntensityGroup={1}></PrepLevelCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-prepLevel1-/)
    expect(getByText('1')).toBeDefined
  })
  it('should return a cell with a classname of prepLevel2 and a text prep level of 2', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <PrepLevelCell areaName={'afton'} meanIntensityGroup={3}></PrepLevelCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-prepLevel2-/)
    expect(getByText('2')).toBeDefined
  })
  it('should return a cell with a classname of prepLevel3 and a text prep level of 3', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <PrepLevelCell areaName={'afton'} meanIntensityGroup={4}></PrepLevelCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-prepLevel3-/)
    expect(getByText('3')).toBeDefined
  })
  it('should return a cell with a classname of prepLevel4 and a text prep level of 4', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <PrepLevelCell areaName={'afton'} meanIntensityGroup={5}></PrepLevelCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-prepLevel4-/)
    expect(getByText('4')).toBeDefined
  })
})
