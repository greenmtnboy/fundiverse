import PortfolioElementModel from "./PortfolioElementModel";
import CashModel from "./CashModel";
import SubPortfolioModel from "./SubPortfolioModel";
import TargetPortfolioModel from "./TargetPortfolioModel";
import { reactive } from "vue";

export default class CompositePortfolioModel {
  name: string;
  loading: boolean;
  holdings: Array<PortfolioElementModel>;
  cash: CashModel;
  /** Cash held at a provider we are currently authenticated to. */
  investable_cash: CashModel;
  target_size: number;
  keys: Array<string>;
  components: Array<SubPortfolioModel>;
  type?: string;
  refreshed_at: number;
  profit_or_loss?: CashModel;
  dividends: CashModel;
  appreciation: CashModel;
  error?: string | null;
  /** At least one provider is showing stale or missing data. */
  partial: boolean;
  degraded_providers: Array<string>;

  constructor({
    name,
    holdings,
    cash,
    target_size,
    components,
    refreshed_at,
    profit_or_loss,
    profit_or_loss_v2,
    dividends,
    appreciation,
    // absent from portfolios persisted before the partial model existed
    investable_cash = null,
    partial = false,
    degraded_providers = [],
  }) {
    this.name = name;
    this.loading = false;
    this.holdings = holdings;
    this.cash = new CashModel(cash);
    // portfolios saved before the partial model existed have no separate
    // investable figure; treat all cash as spendable until a refresh says so
    this.investable_cash = new CashModel(investable_cash ?? cash);
    this.partial = partial ?? false;
    this.degraded_providers = degraded_providers ?? [];
    this.target_size = target_size;
    const scomponents: Array<any> = components as Array<any>;
    this.keys = reactive(
      Object.entries(scomponents).map(([_, component]) => component.provider),
    );
    this.components = reactive(
      Object.entries(scomponents).map(
        ([_, component]) => new SubPortfolioModel(component),
      ),
    );
    this.refreshed_at = refreshed_at;
    if (profit_or_loss && profit_or_loss.value) {
      this.profit_or_loss = new CashModel(profit_or_loss);
    } else {
      this.profit_or_loss = new CashModel({
        currency: "USD",
        value: profit_or_loss,
      });
    }

    if (profit_or_loss_v2) {
      this.dividends = new CashModel(profit_or_loss_v2.dividends);
      this.appreciation = new CashModel(profit_or_loss_v2.appreciation);
    } else {
      this.dividends = new CashModel({ currency: "USD", value: 0.0 });
      this.appreciation = new CashModel({ currency: "USD", value: 0.0 });
    }
    this.error = null;
    if (dividends) {
      this.dividends = new CashModel(dividends);
    }
    if (appreciation) {
      this.appreciation = new CashModel(appreciation);
    }
  }

  /**
   * Snapshots to replay to the backend so providers we are not logged into
   * still count toward composite totals and purchase planning.
   */
  cachedSnapshots() {
    return this.components
      .filter(
        // only replay data we actually fetched at some point; a freshly added
        // provider is a placeholder, not a snapshot
        (component) =>
          component.refreshed_at !== null || component.holdings.length > 0,
      )
      .map((component) => component.toSnapshot());
  }

  /** Providers that can currently take orders. */
  get usableProviders(): Array<string> {
    return this.components
      .filter((component) => !component.isUnusable)
      .map((component) => component.provider);
  }

  get totalValue() {
    return Number(
      this.holdings.reduce(
        (sum, holding) =>
          BigInt(
            sum +
              BigInt(
                Math.floor(parseFloat(holding.value.value || "0") * 10000),
              ),
          ) >> BigInt(0),
        BigInt(0),
      ) / BigInt(10000),
    );
  }

  valueInIndex(index: TargetPortfolioModel) {
    if (!index) {
      return [];
    }
    const indexTickers = index.holdings.reduce(
      (set, holding) => set.add(holding.ticker),
      new Set(),
    );
    return Number(
      this.holdings
        .filter((element) => indexTickers.has(element.ticker))
        .reduce(
          (sum, holding) =>
            BigInt(
              sum +
                BigInt(
                  Math.floor(parseFloat(holding.value.value || "0") * 10000),
                ),
            ) >> BigInt(0),
          BigInt(0),
        ) / BigInt(10000),
    );
  }
}
