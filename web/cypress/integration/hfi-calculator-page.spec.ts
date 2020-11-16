describe('HFI Calculator Page', () => {
  beforeEach(() => {
    cy.server()
    cy.visit('/hfi-calculator/')
  })

  it('Basic Page', () => {
    cy.contains('Hello World!')
  })
})
