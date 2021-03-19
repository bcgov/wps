
describe('Not Found Page', () => {
  beforeEach(() => {
    cy.visit('/notfound')
  })

  it('Basic Page', () => {
    cy.contains('Page Not Found')
  })
})
