# keycloak

Capacitor plugin for keycloak auth

## Install

```bash
npm install keycloak
npx cap sync
```

## API

<docgen-index>

* [`authenticate(...)`](#authenticate)
* [`refreshToken(...)`](#refreshtoken)
* [Interfaces](#interfaces)

</docgen-index>

<docgen-api>
<!--Update the source file JSDoc comments and rerun docgen to update the docs below-->

### authenticate(...)

```typescript
authenticate(options: KeycloakOptions) => Promise<KeycloakAuthResponse>
```

Authenticate against a Keycloak provider.

| Param         | Type                                                        |
| ------------- | ----------------------------------------------------------- |
| **`options`** | <code><a href="#keycloakoptions">KeycloakOptions</a></code> |

**Returns:** <code>Promise&lt;<a href="#keycloakauthresponse">KeycloakAuthResponse</a>&gt;</code>

--------------------


### refreshToken(...)

```typescript
refreshToken(options: KeycloakRefreshOptions) => Promise<KeycloakTokenResponse>
```

Get a new access token based on the given refresh token.

| Param         | Type                                                                      |
| ------------- | ------------------------------------------------------------------------- |
| **`options`** | <code><a href="#keycloakrefreshoptions">KeycloakRefreshOptions</a></code> |

**Returns:** <code>Promise&lt;<a href="#keycloaktokenresponse">KeycloakTokenResponse</a>&gt;</code>

--------------------


### Interfaces


#### KeycloakAuthResponse

| Prop                   | Type                 | Description                                                     |
| ---------------------- | -------------------- | --------------------------------------------------------------- |
| **`isAuthenticated`**  | <code>boolean</code> | Indicates whether authentication was successful                 |
| **`accessToken`**      | <code>string</code>  | The access token (if authentication was successful)             |
| **`refreshToken`**     | <code>string</code>  | The refresh token (if provided by the server)                   |
| **`idToken`**          | <code>string</code>  | The ID token (if provided by the server and requested in scope) |
| **`tokenType`**        | <code>string</code>  | Token type, typically "Bearer"                                  |
| **`expiresIn`**        | <code>number</code>  | Token expiration time in seconds                                |
| **`scope`**            | <code>string</code>  | The scope granted by the authorization server                   |
| **`error`**            | <code>string</code>  | Error code (if authentication failed)                           |
| **`errorDescription`** | <code>string</code>  | Error description (if authentication failed)                    |
| **`redirectUrl`**      | <code>string</code>  | The redirect URL used                                           |


#### KeycloakOptions

| Prop                       | Type                | Description                                                                                                                                         |
| -------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`clientId`**             | <code>string</code> | The client id you get from the keycloak server... required!                                                                                         |
| **`authorizationBaseUrl`** | <code>string</code> | The base url for retrieving tokens depending on the response type from a OAuth 2 provider. e.g. https://accounts.google.com/o/oauth2/auth required! |
| **`redirectUrl`**          | <code>string</code> | Url to which the oauth provider redirects after authentication. required!                                                                           |
| **`accessTokenEndpoint`**  | <code>string</code> | Url for retrieving the access_token by the authorization code flow. required!                                                                       |


#### KeycloakTokenResponse

| Prop               | Type                | Description                                   |
| ------------------ | ------------------- | --------------------------------------------- |
| **`accessToken`**  | <code>string</code> | The new access token                          |
| **`refreshToken`** | <code>string</code> | The new refresh token (if provided)           |
| **`tokenType`**    | <code>string</code> | Token type, typically "Bearer"                |
| **`expiresIn`**    | <code>number</code> | Token expiration time in seconds              |
| **`scope`**        | <code>string</code> | The scope granted by the authorization server |


#### KeycloakRefreshOptions

| Prop                      | Type                | Description                                                                      |
| ------------------------- | ------------------- | -------------------------------------------------------------------------------- |
| **`clientId`**            | <code>string</code> | The app id (client id) you get from the oauth provider like Google, Facebook,... |
| **`accessTokenEndpoint`** | <code>string</code> | Url for retrieving the access_token.                                             |
| **`refreshToken`**        | <code>string</code> | The refresh token that will be used to obtain the new access token.              |

</docgen-api>
