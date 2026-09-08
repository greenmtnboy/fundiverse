## Webull Setup

Webull access uses Webull's official
[OpenAPI SDK](https://developer.webull.com/api-doc/), so you authenticate with
an app key and app secret rather than your account password.

### Prod

Create an account on Webull as normal, then:

1. Apply for OpenAPI access in the
   [Webull developer portal](https://developer.webull.com/) for your region.
2. Generate an app key / app secret pair.
3. Subscribe the credentials to the brokerage account you want Fundiverse to
   trade. If the credentials cover more than one account, Fundiverse uses the
   first one returned.

To login to webull in the app, you will need

- app key
- app secret

Add a provider and select webull, then fill in the fields.

::: warning
Webull's OpenAPI has no paper trading mode, so `webull_paper` is no longer an
available provider. It also exposes no dividend or transaction history
endpoints, so profit reporting for Webull holdings covers appreciation only.
:::
