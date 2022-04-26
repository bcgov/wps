import { Table, TableBody, TableContainer, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import MeanPrepLevelCell from 'features/hfiCalculator/components/MeanPrepLevelCell'
import React from 'react'

const renderMeanPrepLevel = (prepLevel: number | undefined, invalidForecast: boolean) => {
  return render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <MeanPrepLevelCell
              testid={'weekly-prep-level-afton'}
              areaName={'test'}
              meanPrepLevel={prepLevel}
              emptyOrIncompleteForecast={invalidForecast}
            ></MeanPrepLevelCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

describe('meanPrepLevelCell', () => {
  it('should return a cell with a classname of prepLevel1 and a text prep level of 1', () => {
    const { getByTestId } = renderMeanPrepLevel(1, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel1-/)
    expect(cell.innerHTML).toBe('1')
  })
  it('should return a cell with a classname of prepLevel2 and a text prep level of 2', () => {
    const { getByTestId } = renderMeanPrepLevel(2, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel2-/)
    expect(cell.innerHTML).toBe('2')
  })
  it('should return a cell with a classname of prepLevel3 and a text prep level of 3', () => {
    const { getByTestId } = renderMeanPrepLevel(3, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel3-/)
    expect(cell.innerHTML).toBe('3')
  })
  it('should return a cell with a classname of prepLevel4 and a text prep level of 4', () => {
    const { getByTestId } = renderMeanPrepLevel(4, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel4-/)
    expect(cell.innerHTML).toBe('4')
  })
  it('should return a cell with a classname of prepLevel5 and a text prep level of 5', () => {
    const { getByTestId } = renderMeanPrepLevel(5, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel5-/)
    expect(cell.innerHTML).toBe('5')
  })
  it('should return a cell with a classname of prepLevel6 and a text prep level of 6', () => {
    const { getByTestId } = renderMeanPrepLevel(6, false)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-meanPrepLevel6-/)
    expect(cell.innerHTML).toBe('6')
  })
  it('should return a cell with a classname of defaultBackground and a text prep level undefined', () => {
    const { getByTestId } = renderMeanPrepLevel(undefined, true)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/makeStyles-defaultBackground-/)
    const errorIcon = getByTestId('prep-level-error')
    expect(errorIcon).toBeDefined()
  })
})
