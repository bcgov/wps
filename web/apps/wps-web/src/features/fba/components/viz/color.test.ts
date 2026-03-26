import { getColorByFuelTypeCode } from 'features/fba/components/viz/color'

const colorByFuelTypeCodeTestMap = new Map()
colorByFuelTypeCodeTestMap.set('C-1', 'rgb(209, 255, 115)')
colorByFuelTypeCodeTestMap.set('C-2', 'rgb(34, 102, 51)')
colorByFuelTypeCodeTestMap.set('C-3', 'rgb(131, 199, 149)')
colorByFuelTypeCodeTestMap.set('C-4', 'rgb(112, 168, 0)')
colorByFuelTypeCodeTestMap.set('C-5', 'rgb(223, 184, 230)')
colorByFuelTypeCodeTestMap.set('C-6', 'rgb(172, 102, 237)')
colorByFuelTypeCodeTestMap.set('C-7', 'rgb(112, 12, 242)')
colorByFuelTypeCodeTestMap.set('D-1/D-2', 'rgb(137, 112, 68)')
colorByFuelTypeCodeTestMap.set('S-1', 'rgb(251, 190, 185)')
colorByFuelTypeCodeTestMap.set('S-2', 'rgb(247, 104, 161)')
colorByFuelTypeCodeTestMap.set('S-3', 'rgb(174, 1, 126)')
colorByFuelTypeCodeTestMap.set('O-1a/O-1b', 'rgb(255, 255, 190)')
colorByFuelTypeCodeTestMap.set('M-1/M-2', 'rgb(255, 211, 127)')

describe('getColorByFuelTypeCode', () => {
  it('should return the correct colour for each fuel type code', () => {
    const keys = colorByFuelTypeCodeTestMap.keys()
    for (const key of keys) {
      expect(getColorByFuelTypeCode(key)).toBe(colorByFuelTypeCodeTestMap.get(key))
    }
  })
  it('should return a default color when a matching key is not found', () => {
    expect(getColorByFuelTypeCode('foo')).toBe('rgb(0, 255, 255)')
  })
})
