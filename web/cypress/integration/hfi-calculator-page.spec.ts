import { HFI_CALC_ROUTE } from '../../src/utils/constants'

describe('HFI Calculator Page', () => {
  beforeEach(() => {
    cy.server()
    cy.visit(HFI_CALC_ROUTE)
  })

  it('Basic Page', () => {
    cy.contains('Hello World!')
  })
})
