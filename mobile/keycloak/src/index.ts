import { registerPlugin } from '@capacitor/core';

import type { KeycloakPlugin } from './definitions';

const Keycloak = registerPlugin<KeycloakPlugin>('Keycloak', {
  web: () => import('./web').then((m) => new m.KeycloakWeb()),
});

export * from './definitions';
export { Keycloak };
