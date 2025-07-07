# keycloak

Capacitor plugin for keycloak auth

## Install

```bash
npm install keycloak
npx cap sync
```

## API

<docgen-index>

* [`echo(...)`](#echo)
* [`authenticate(...)`](#authenticate)
* [`refreshToken(...)`](#refreshtoken)
* [Interfaces](#interfaces)

</docgen-index>

<docgen-api>
<!--Update the source file JSDoc comments and rerun docgen to update the docs below-->

### echo(...)

```typescript
echo(options: { value: string; }) => Promise<{ value: string; }>
```

| Param         | Type                            |
| ------------- | ------------------------------- |
| **`options`** | <code>{ value: string; }</code> |

**Returns:** <code>Promise&lt;{ value: string; }&gt;</code>

--------------------


### authenticate(...)

```typescript
authenticate(options: KeycloakOptions) => Promise<any>
```

Authenticate against a Keycloak provider.

| Param         | Type                                                        |
| ------------- | ----------------------------------------------------------- |
| **`options`** | <code><a href="#keycloakoptions">KeycloakOptions</a></code> |

**Returns:** <code>Promise&lt;any&gt;</code>

--------------------


### refreshToken(...)

```typescript
refreshToken(options: KeycloakRefreshOptions) => Promise<any>
```

Get a new access token based on the given refresh token.

| Param         | Type                                                                      |
| ------------- | ------------------------------------------------------------------------- |
| **`options`** | <code><a href="#keycloakrefreshoptions">KeycloakRefreshOptions</a></code> |

**Returns:** <code>Promise&lt;any&gt;</code>

--------------------


### Interfaces


#### KeycloakOptions

| Prop                            | Type                                    | Description                                                                                                                                                                                                                                            | Since                          |
| ------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------ |
| **`clientId`**                  | <code>string</code>                     | The client id you get from the keycloak server... required!                                                                                                                                                                                            |                                |
| **`authorizationBaseUrl`**      | <code>string</code>                     | The base url for retrieving tokens depending on the response type from a OAuth 2 provider. e.g. https://accounts.google.com/o/oauth2/auth required!                                                                                                    |                                |
| **`responseType`**              | <code>string</code>                     | Tells the authorization server which grant to execute. Be aware that a full code flow is not supported as clientCredentials are not included in requests. But you can retrieve the authorizationCode if you don't set a accessTokenEndpoint. required! |                                |
| **`redirectUrl`**               | <code>string</code>                     | Url to which the oauth provider redirects after authentication. required!                                                                                                                                                                              |                                |
| **`accessTokenEndpoint`**       | <code>string</code>                     | Url for retrieving the access_token by the authorization code flow.                                                                                                                                                                                    |                                |
| **`resourceUrl`**               | <code>string</code>                     | Protected resource url. For authentication you only need the basic user details.                                                                                                                                                                       |                                |
| **`pkceEnabled`**               | <code>boolean</code>                    | Enable PKCE if you need it.                                                                                                                                                                                                                            |                                |
| **`scope`**                     | <code>string</code>                     | A space-delimited list of permissions that identify the resources that your application could access on the user's behalf. If you want to get a refresh token, you most likely will need the offline_access scope (only supported in Code Flow!)       |                                |
| **`state`**                     | <code>string</code>                     | A unique alpha numeric string used to prevent CSRF. If not set the plugin automatically generate a string and sends it as using state is recommended.                                                                                                  |                                |
| **`additionalParameters`**      | <code>{ [key: string]: string; }</code> | Additional parameters for the created authorization url                                                                                                                                                                                                |                                |
| **`logsEnabled`**               | <code>boolean</code>                    |                                                                                                                                                                                                                                                        | 3.0.0                          |
| **`logoutUrl`**                 | <code>string</code>                     |                                                                                                                                                                                                                                                        | 3.1.0 ... not implemented yet! |
| **`additionalResourceHeaders`** | <code>{ [key: string]: string; }</code> | Additional headers for resource url request                                                                                                                                                                                                            | 3.0.0                          |


#### KeycloakRefreshOptions

| Prop                      | Type                | Description                                                                      |
| ------------------------- | ------------------- | -------------------------------------------------------------------------------- |
| **`clientId`**            | <code>string</code> | The app id (client id) you get from the oauth provider like Google, Facebook,... |
| **`accessTokenEndpoint`** | <code>string</code> | Url for retrieving the access_token.                                             |
| **`refreshToken`**        | <code>string</code> | The refresh token that will be used to obtain the new access token.              |

</docgen-api>
