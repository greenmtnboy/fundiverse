## Schwab Setup

::: warning
Robinhood access uses a open-source library that is not officially supported by Schwab, [schwab-py](https://github.com/alexgolec/schwab-py). Ensure you are comfortable with this library as well.
:::


### Prod


Following the [schwab-py instructions for setting up an account](https://schwab-py.readthedocs.io/en/latest/getting-started.html#schwab-api-access). Once your application is approved and you have an api_key and app_secret, you can log in per normal in the Fundiverse flow by adding schwab as a provider.

Your first login will open a popup to the schwab registration to complete the auth flow. Once you close it, resubmit the login form. You can refresh/reconnect without doing this flow again for up to a week currently.