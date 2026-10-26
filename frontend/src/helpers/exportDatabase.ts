import instance from '/src/api/instance'
import store from '/src/store'

export interface DatabaseExportResult {
    database_path: string
    portfolio_name: string
    providers_processed: Array<string>
    total_holdings: number
    total_dividends: number
    /** providers in the portfolio we are not authenticated to */
    providers_skipped: Array<string>
}

/** Build the portfolio's DuckDB file on the backend.
 *
 * Sends the portfolio's own providers; left empty, the backend would export
 * only providers whose holdings happen to be cached, silently dropping any
 * that have not loaded yet.
 */
export async function requestDatabaseExport(
    portfolioName: string,
): Promise<DatabaseExportResult> {
    const portfolio = store.getters.compositePortfolios.find(
        (p: { name: string }) => p.name === portfolioName,
    )
    const response = await instance.post(`database/export_portfolio_database`, {
        portfolio_name: portfolioName,
        providers: portfolio?.keys ?? [],
    })
    return response.data
}
