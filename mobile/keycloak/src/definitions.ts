export interface KeycloakPlugin {
  /**
   * Authenticate against a Keycloak provider.
   * @param {KeycloakOptions} options
   * @returns {Promise<KeycloakAuthResponse>} the authentication response
   */
  authenticate(options: KeycloakOptions): Promise<KeycloakAuthResponse>;
  /**
   * Add a listener for plugin events, specifically for token refreshes.
   * @param {string} eventName
   * @param {Function} listenerFunc
   */
  addListener(eventName: string, listenerFunc: (data: any) => void): Promise<void>;
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
   *
   * required!
   */
  accessTokenEndpoint: string;
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

export interface KeycloakAuthResponse {
  /**
   * Indicates whether authentication was successful
   */
  isAuthenticated: boolean;
  /**
   * The access token (if authentication was successful)
   */
  accessToken?: string;
  /**
   * The refresh token (if provided by the server)
   */
  refreshToken?: string;
  /**
   * The ID token (if provided by the server and requested in scope)
   */
  idToken?: string;
  /**
   * Token type, typically "Bearer"
   */
  tokenType?: string;
  /**
   * Token expiration time in seconds
   */
  expiresIn?: number;
  /**
   * The scope granted by the authorization server
   */
  scope?: string;
  /**
   * Error code (if authentication failed)
   */
  error?: string;
  /**
   * Error description (if authentication failed)
   */
  errorDescription?: string;
  /**
   * The redirect URL used
   */
  redirectUrl?: string;
  /**
   * Additional response data
   */
  [key: string]: any;
}

export interface KeycloakTokenResponse {
  /**
   * The new access token
   */
  accessToken: string;
  /**
   * The new refresh token (if provided)
   */
  refreshToken?: string;
  /**
   * Token type, typically "Bearer"
   */
  tokenType?: string;
  /**
   * Token expiration time in seconds
   */
  expiresIn?: number;
  /**
   * The scope granted by the authorization server
   */
  scope?: string;
  /**
   * Additional token response data
   */
  [key: string]: any;
}
