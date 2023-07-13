import { Table, TableBody, TableContainer, TableRow } from '@mui/material'
import { render } from '@testing-library/react'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import React from 'react'

const renderPrepLevel = (prepLevel: number | undefined) => {
  return render(
    <TableContainer>
      <Table>
        <TableBody>
          <TableRow>
            <PrepLevelCell testid={'weekly-prep-level-afton'} toolTipText="test" prepLevel={prepLevel}></PrepLevelCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  )
}

describe('PrepLevelCell', () => {
  it('should return a cell with a classname of prepLevel1 and a text prep level of 1', () => {
    const { getByTestId } = renderPrepLevel(1)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel1/)
    expect(cell.innerHTML).toBe('1')
  })
  it('should return a cell with a classname of prepLevel2 and a text prep level of 2', () => {
    const { getByTestId } = renderPrepLevel(2)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel2/)
    expect(cell.innerHTML).toBe('2')
  })
  it('should return a cell with a classname of prepLevel3 and a text prep level of 3', () => {
    const { getByTestId } = renderPrepLevel(3)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel3/)
    expect(cell.innerHTML).toBe('3')
  })
  it('should return a cell with a classname of prepLevel4 and a text prep level of 4', () => {
    const { getByTestId } = renderPrepLevel(4)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel4/)
    expect(cell.innerHTML).toBe('4')
  })
  it('should return a cell with a classname of prepLevel5 and a text prep level of 5', () => {
    const { getByTestId } = renderPrepLevel(5)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel5/)
    expect(cell.innerHTML).toBe('5')
  })
  it('should return a cell with a classname of prepLevel6 and a text prep level of 6', () => {
    const { getByTestId } = renderPrepLevel(6)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevel6/)
    expect(cell.innerHTML).toBe('6')
  })
  it('should return a cell with a classname of defaultBackground and a text prep level undefined', () => {
    const { getByTestId } = renderPrepLevel(undefined)
    const cell = getByTestId('weekly-prep-level-afton')
    expect(cell.className).toMatch(/prepLevelDefault/)
    const errorIcon = getByTestId('prep-level-error')
    expect(errorIcon).toBeDefined()
  })
})
