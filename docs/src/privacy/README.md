# Privacy Policy

#### Last updated: October 23, 2026

<br/>
This Privacy Policy describes how fundiverse ("we", "us", or "our") handles personal
information across three things: the website at fundiverse.dev, the fundiverse desktop
application, and finplan, a companion command-line planning tool in the fundiverse
family. The short version: the website collects basic analytics; the applications run
entirely on your own computer and send nothing to us.

## The website (fundiverse.dev)

We collect tracking info on the website to understand visit counts and whether people
reach key demo interaction points. It's currently Google Analytics but we'd like to move
to something better (more privacy focused). No account is required to browse the site
and we do not sell or share analytics data.

## The fundiverse desktop application

fundiverse is open-source software you download and run on your own computer. It has no
server operated by us and no fundiverse account.

- **Brokerage credentials.** When you log in to a brokerage inside the app, your
  credentials or OAuth tokens are sent from your computer directly to that brokerage.
  They are never sent to fundiverse. The app keeps brokerage sessions in memory while it
  is running; some brokerage client libraries cache a session token locally on your
  device so you do not have to log in every time.
- **Portfolio data.** Holdings, prices, and dividends are fetched from your brokerage to
  your computer to build and compare portfolios. If you use the "export portfolio
  database" feature, that data is written to a local file under your home directory
  (`~/.fundiverse/databases/`). It stays on your device.
- **Trades.** Orders you place through the app go from your computer to your brokerage.
  We do not see them. Money never leaves your brokerage.
- **No telemetry.** The desktop application does not send usage data, crash reports, or
  any personal information to us.

## finplan (companion planning tool)

finplan is a command-line tool, also run only on your own computer, that combines
brokerage exports with bank and card transactions to analyse spending and estimate a
sustainable retirement withdrawal rate. It can connect to banks through Plaid.

- **Single operator, local only.** The person who runs finplan is the only person whose
  data it touches, and that data is stored only on their computer. There is no hosted
  service, no user accounts, and no multi-tenancy. Each person who runs finplan uses
  their own Plaid developer credentials and their own linked institutions; we never
  receive, proxy, or have access to anyone else's tokens or financial data.
- **What is collected through Plaid.** With your explicit action and consent in Plaid
  Link: institution and account names, account type, the last digits of the account
  number, transactions (date, amount, description, category) and current balances.
  Bank credentials are entered only into Plaid Link or your bank's own sign-in page,
  never into finplan. finplan requests Plaid's `transactions` product only; it does not
  request identity, income, authentication, liabilities, or investment data, and it
  never initiates payments or trades. Plaid's handling of your data is governed by
  [Plaid's End User Privacy Policy](https://plaid.com/legal/#end-user-privacy-policy),
  shown in Plaid Link before any account is connected.
- **What is collected from files.** Brokerage and bank CSV exports you choose to place
  in finplan's data folder.
- **Use.** Solely to produce your own spending analysis, portfolio summary, and
  retirement forecast. No advertising, profiling, sale, or sharing.
- **Storage and access.** All data stays in a local database and local files on your
  computer, on an encrypted drive, readable by your operating-system account only.
  finplan never uploads data to a server, cloud storage, or backup service. The only
  third party involved is Plaid Inc., as the data access provider between your
  financial institutions and the tool. Outbound network traffic from finplan goes to
  Plaid's API over TLS 1.2 or better and nowhere else.
- **Consent.** Data is collected only when you deliberately run the link command, pick
  an institution in Plaid Link, accept Plaid's consent screen, and authenticate with
  the institution (including the institution's own OAuth consent page where it has
  one). Every later sync is an explicit command you run. You withdraw consent by
  unlinking the institution, which revokes finplan's access at Plaid.
- **Retention and deletion.** Financial history is kept locally for as long as you find
  it useful for planning; multi-year history is the point of the tool, so there is no
  automatic expiry and retention is your choice. Deletion is complete and immediate:
  `finplan plaid unlink <institution> --purge` revokes the Plaid connection via Plaid's
  item removal endpoint and deletes that institution's data locally; deleting the data
  directory removes everything; deleting the `.env` file removes the Plaid credentials.
  No copies exist anywhere else. This policy and the retention practice are reviewed at
  least annually and whenever a new data source is added.
- **Your rights.** Because you are the sole data subject and hold the data directly, the
  rights granted by privacy laws such as the CCPA and GDPR (access, correction, deletion,
  portability, withdrawal of consent) are exercised directly on your own files and
  through the commands above. No data is sold or shared.

## Children

None of these services are directed at children under 13 and we do not knowingly
collect information from them.

## Changes

We will post any changes to this policy on this page and update the date at the top.

### Contact

<br/>
Should you have any questions about our privacy practices or this Privacy Policy, or if
you would like to exercise any of the rights available to you, please email us at
fundiverse.community@gmail.com.

<br/>
For the purpose of applicable data protection laws, we are the data controller of
personal information collected by the website. For the desktop application and finplan,
the person operating the software on their own computer controls their own data; we
process none of it. Our representative is fundiverse.community@gmail.com.
