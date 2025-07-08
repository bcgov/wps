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

| Prop                       | Type                | Description                                                                                                                                         |
| -------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`clientId`**             | <code>string</code> | The client id you get from the keycloak server... required!                                                                                         |
| **`authorizationBaseUrl`** | <code>string</code> | The base url for retrieving tokens depending on the response type from a OAuth 2 provider. e.g. https://accounts.google.com/o/oauth2/auth required! |
| **`redirectUrl`**          | <code>string</code> | Url to which the oauth provider redirects after authentication. required!                                                                           |
| **`accessTokenEndpoint`**  | <code>string</code> | Url for retrieving the access_token by the authorization code flow.                                                                                 |


#### KeycloakRefreshOptions

| Prop                      | Type                | Description                                                                      |
| ------------------------- | ------------------- | -------------------------------------------------------------------------------- |
| **`clientId`**            | <code>string</code> | The app id (client id) you get from the oauth provider like Google, Facebook,... |
| **`accessTokenEndpoint`** | <code>string</code> | Url for retrieving the access_token.                                             |
| **`refreshToken`**        | <code>string</code> | The refresh token that will be used to obtain the new access token.              |

</docgen-api>
