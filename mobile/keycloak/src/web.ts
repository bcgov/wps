import { WebPlugin } from '@capacitor/core';

import type { KeycloakPlugin, KeycloakOptions, KeycloakRefreshOptions } from './definitions';

export class KeycloakWeb extends WebPlugin implements KeycloakPlugin {
  async authenticate(options: KeycloakOptions): Promise<any> {
    console.log('Keycloak Web: Starting authentication', options);

    // Build the authorization URL
    const params = new URLSearchParams({
      client_id: options.clientId,
      response_type: options.responseType || 'code',
      redirect_uri: options.redirectUrl || `${window.location.origin}/keycloak/callback`,
      scope: options.scope || 'openid',
      state: options.state || this.generateRandomString(32),
    });

    // Add additional parameters
    if (options.additionalParameters) {
      Object.entries(options.additionalParameters).forEach(([key, value]) => {
        params.append(key, value);
      });
    }

    const authUrl = `${options.authorizationBaseUrl}?${params.toString()}`;

    if (options.logsEnabled) {
      console.log('Keycloak: Authorization URL:', authUrl);
    }

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
          scope: options.scope || 'openid',
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

  private generateRandomString(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }
}
