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
   * Tells the authorization server which grant to execute. Be aware that a full code flow is not supported as clientCredentials are not included in requests.
   *
   * But you can retrieve the authorizationCode if you don't set a accessTokenEndpoint.
   *
   * required!
   */
  responseType?: string;
  /**
   * Url to  which the oauth provider redirects after authentication.
   *
   * required!
   */
  redirectUrl?: string;
  /**
   * Url for retrieving the access_token by the authorization code flow.
   */
  accessTokenEndpoint?: string;
  /**
   * Protected resource url. For authentication you only need the basic user details.
   */
  resourceUrl?: string;
  /**
   * Enable PKCE if you need it.
   */
  pkceEnabled?: boolean;
  /**
   * A space-delimited list of permissions that identify the resources that your application could access on the user's behalf.
   * If you want to get a refresh token, you most likely will need the offline_access scope (only supported in Code Flow!)
   */
  scope?: string;
  /**
   * A unique alpha numeric string used to prevent CSRF. If not set the plugin automatically generate a string
   * and sends it as using state is recommended.
   */
  state?: string;
  /**
   * Additional parameters for the created authorization url
   */
  additionalParameters?: { [key: string]: string };
  /**
   * @since 3.0.0
   */
  logsEnabled?: boolean;
  /**
   * @since 3.1.0 ... not implemented yet!
   */
  logoutUrl?: string;

  /**
   * Additional headers for resource url request
   * @since 3.0.0
   */
  additionalResourceHeaders?: { [key: string]: string };
}
