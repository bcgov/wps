import { WebPlugin } from '@capacitor/core';

import type { KeycloakOptions, KeycloakAuthResponse } from './definitions';

export class KeycloakWeb extends WebPlugin {
  async authenticate(options: KeycloakOptions): Promise<KeycloakAuthResponse> {
    console.log('Keycloak Web: Starting authentication', options);

    return {
      isAuthenticated: false,
      error: 'not_implemented',
      errorDescription: 'Not implemented',
    };
  }
}
