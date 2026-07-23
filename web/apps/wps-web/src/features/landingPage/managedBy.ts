export interface ManagedByInfo {
  name: string
  href?: string
  opensFeedback?: boolean
}

export const CSBC_PREDICTIVE_SERVICES_MANAGED_BY: ManagedByInfo = {
  name: 'CSBC - Predictive Services',
  opensFeedback: true
}

const BCWS_PREDICTIVE_SERVICES_EMAIL = 'BCWS.PredictiveServices@gov.bc.ca'

export const BCWS_PREDICTIVE_SERVICES_MANAGED_BY: ManagedByInfo = {
  name: 'BCWS - Predictive Services',
  href: `mailto:${BCWS_PREDICTIVE_SERVICES_EMAIL}`
}

export const BCWS_PREDICTIVE_SERVICES_CONTACT_HREF = `mailto:${BCWS_PREDICTIVE_SERVICES_EMAIL}`
