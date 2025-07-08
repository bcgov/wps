export interface KeycloakPlugin {
  echo(options: { value: string }): Promise<{ value: string }>;

  /**
   * Authenticate against a Keycloak provider.
   * @param {KeycloakOptions} options
   * @returns {Promise<any>} the resource url response
   */
  authenticate(options: KeycloakOptions): Promise<any>;
  /**
   * Get a new access token based on the given refresh token.
   * @param {KeycloakRefreshOptions} options
   * @returns {Promise<any>} the token endpoint response
   */
  refreshToken(options: KeycloakRefreshOptions): Promise<any>;
}

export interface KeycloakOptions {
  /**
   * The client id you get from the keycloak server...
   *
   * required!
   */
  clientId: string;
  /**
   * The base url for retrieving tokens depending on the response type from a OAuth 2 provider. e.g. https://accounts.google.com/o/oauth2/auth
   *
   * required!
   */
  authorizationBaseUrl: string;
  /**
   * Url to  which the oauth provider redirects after authentication.
   *
   * required!
   */
  redirectUrl: string;
  /**
   * Url for retrieving the access_token by the authorization code flow.
   */
  accessTokenEndpoint?: string;
}

export interface KeycloakRefreshOptions {
  /**
   * The app id (client id) you get from the oauth provider like Google, Facebook,...
   */
  clientId: string;
  /**
   * Url for retrieving the access_token.
   */
  accessTokenEndpoint: string;
  /**
   * The refresh token that will be used to obtain the new access token.
   */
  refreshToken: string;
}
