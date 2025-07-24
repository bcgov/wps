import { KeycloakPlugin } from '@/keycloak/definitions';
import { registerPlugin } from '@capacitor/core';

const Keycloak = registerPlugin<KeycloakPlugin>('Keycloak', {
  web: () => import('./web').then((m) => new m.KeycloakWeb()),
});

export * from './definitions';
export { Keycloak };
