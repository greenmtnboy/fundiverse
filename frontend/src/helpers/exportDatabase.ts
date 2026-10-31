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
    /** providers whose login expired mid-export, with the broker's error */
    provider_errors: Record<string, string>
    composition_included: boolean
    composition_error: string | null
}

/** The portfolio's index and customizations, so the export carries the
 * target it is measured against. */
function portfolioComposition(portfolioName: string, targetSize?: number) {
    const custom = store.getters.getCustomizationByName(portfolioName)
    if (!custom) {
        return null
    }
    return {
        index: custom.indexPortfolio || null,
        target_size: targetSize ?? null,
        reweight: Boolean(custom.reweightIndex),
        stock_exclusions: Array.from(custom.excludedTickers),
        list_exclusions: Array.from(custom.excludedLists),
        stock_modifications: custom.stockModifications,
        list_modifications: custom.listModifications,
    }
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
        composition: portfolioComposition(portfolioName, portfolio?.target_size),
    })
    return response.data
}
