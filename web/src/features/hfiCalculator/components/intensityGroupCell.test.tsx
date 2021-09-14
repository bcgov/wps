import { TableContainer, Table, TableRow, TableBody } from '@material-ui/core'
import { render } from '@testing-library/react'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import React from 'react'
describe('IntensityGroupCell', () => {
  it('should return cell with value 1 and color code 1', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <IntensityGroupCell
                testid={'value1-color1'}
                value={1}
                error={false}
              ></IntensityGroupCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('value1-color1')).toHaveClass(
      'makeStyles-intensityGroupOutline1-1'
    )
    expect(getByText('1')).toBeDefined
  })
  it('should return cell with value 2 and color code 2', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <IntensityGroupCell
                testid={'value2-color2'}
                value={2}
                error={false}
              ></IntensityGroupCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('value2-color2')).toHaveClass(
      'makeStyles-intensityGroupOutline2-7'
    )
    expect(getByText('2')).toBeDefined
  })
  it('should return cell with value 3 and color code 3', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <IntensityGroupCell
                testid={'value3-color3'}
                value={3}
                error={false}
              ></IntensityGroupCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('value3-color3')).toHaveClass(
      'makeStyles-intensityGroupOutline3-13'
    )
    expect(getByText('3')).toBeDefined
  })
  it('should return cell with value 4 and color code 4', () => {
    const { getByTestId, getByText } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <IntensityGroupCell
                testid={'value4-color4'}
                value={4}
                error={false}
              ></IntensityGroupCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('value4-color4')).toHaveClass(
      'makeStyles-intensityGroupOutline4-19'
    )
    expect(getByText('4')).toBeDefined
  })
  it('should return cell with no value and no color coding', () => {
    const { getByTestId } = render(
      <TableContainer>
        <Table>
          <TableBody>
            <TableRow>
              <IntensityGroupCell
                testid={'no-value'}
                value={undefined}
                error={false}
              ></IntensityGroupCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    )
    expect(getByTestId('no-value')).toHaveStyle({
      border: ''
    })
  })
})
