## E*TRADE Setup

::: warning
E*TRADE API access requires requesting an API key from E*TRADE and agreeing to their developer terms. The API only supports whole-share orders, so E*TRADE portfolios rebalance with less precision than fractional-share providers.
:::

### Getting keys

Request an API key and secret from the [E*TRADE developer portal](https://developer.etrade.com/home). You will initially receive sandbox keys; production keys are issued after E*TRADE reviews your request.

### Logging in

Add E*TRADE as a provider in Fundiverse and enter your API key (consumer key) and secret. If you are using sandbox keys, enter `true` in the sandbox field.

E*TRADE uses OAuth 1.0a, which requires a browser authorization on first login:

1. Submit the login form. A link to E*TRADE will appear - open it and sign in to authorize Fundiverse.
2. E*TRADE will display a short verification code. Paste it into the Verification Code field and click Authenticate again.

E*TRADE access tokens expire at midnight US Eastern, so expect to repeat the authorization once per day. Within the same day, Fundiverse renews the token automatically.

### Automatic callback (optional)

By default E*TRADE only supports the paste-a-code flow described above. If you ask [E*TRADE API support](mailto:etradeapi@etrade.com) to register the callback URL `http://localhost:3042/public/etrade/callback` for your consumer key, the authorization completes automatically when E*TRADE redirects your browser back to Fundiverse - no code pasting needed. After the browser shows "authorization complete", click Authenticate again.
