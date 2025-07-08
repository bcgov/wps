import { WebPlugin } from '@capacitor/core';

import type { KeycloakPlugin, KeycloakOptions, KeycloakRefreshOptions } from './definitions';

export class KeycloakWeb extends WebPlugin implements KeycloakPlugin {
  async authenticate(options: KeycloakOptions): Promise<any> {
    console.log('Keycloak Web: Starting authentication', options);

    // Build the authorization URL
    const params = new URLSearchParams({
      client_id: options.clientId,
      response_type: 'code',
      redirect_uri: options.redirectUrl || `${window.location.origin}/keycloak/callback`,
    });

    const authUrl = `${options.authorizationBaseUrl}?${params.toString()}`;
    console.log(authUrl);

    // For web, we'll simulate the authentication flow
    // In a real implementation, you would redirect to the auth URL or open a popup
    return new Promise((resolve) => {
      // Mock response for demonstration
      setTimeout(() => {
        const mockResponse = {
          access_token: `web_mock_token_${Date.now()}`,
          token_type: 'Bearer',
          expires_in: 3600,
          refresh_token: `web_mock_refresh_${Date.now()}`,
          state: params.get('state'),
        };

        console.log('Keycloak Web: Authentication successful', mockResponse);
        resolve(mockResponse);
      }, 1000);
    });
  }

  async refreshToken(options: KeycloakRefreshOptions): Promise<any> {
    console.log('Keycloak Web: Refreshing token', { clientId: options.clientId });

    // In a real implementation, you would make a POST request to the token endpoint
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockResponse = {
          access_token: `web_refreshed_token_${Date.now()}`,
          token_type: 'Bearer',
          expires_in: 3600,
          refresh_token: options.refreshToken,
          scope: 'openid',
        };

        console.log('Keycloak Web: Token refresh successful', mockResponse);
        resolve(mockResponse);
      }, 500);
    });
  }

  async echo(options: { value: string }): Promise<{ value: string }> {
    console.log('ECHO', options);
    return options;
  }
}
