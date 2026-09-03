import PortfolioElementModel from "./PortfolioElementModel";
import CashModel from "./CashModel";
import { reactive } from "vue";

/** Mirrors the backend ProviderStatus enum. */
export const ProviderStatus = {
  REFRESHED: "refreshed",
  CACHED: "cached",
  UNAUTHENTICATED: "unauthenticated",
  ERROR: "error",
} as const;

export type ProviderStatusValue =
  (typeof ProviderStatus)[keyof typeof ProviderStatus];

export default class SubPortfolioModel {
  name: string;
  holdings: Array<PortfolioElementModel>;
  cash: CashModel;
  target_size: number;
  provider: string;
  loading: boolean;
  profit_or_loss: CashModel;
  dividends: CashModel;
  appreciation: CashModel;
  status: ProviderStatusValue;
  error: string | null;
  refreshed_at: number | null;

  constructor({
    name,
    holdings,
    cash,
    target_size,
    provider,
    profit_or_loss_v2,
    profit_or_loss,
    dividends,
    appreciation,
    // absent from sub-portfolios persisted before the partial model existed
    status = null,
    error = null,
    refreshed_at = null,
  }) {
    this.name = name;
    this.holdings = reactive(holdings);
    this.cash = new CashModel(cash);
    this.target_size = target_size;
    this.provider = provider;
    this.loading = false;
    this.profit_or_loss = profit_or_loss;
    if (profit_or_loss_v2) {
      this.dividends = new CashModel(profit_or_loss_v2.dividends);
      this.appreciation = new CashModel(profit_or_loss_v2.appreciation);
    } else {
      this.dividends = new CashModel({ currency: "USD", value: 0.0 });
      this.appreciation = new CashModel({ currency: "USD", value: 0.0 });
    }
    if (dividends) {
      this.dividends = new CashModel(dividends)
    }
    if (appreciation) {
      this.appreciation = new CashModel(appreciation)
    }
    // portfolios persisted before per-provider status existed load as
    // "cached", which is exactly what they are
    this.status = status ?? ProviderStatus.CACHED;
    this.error = error ?? null;
    this.refreshed_at = refreshed_at ?? null;
  }

  /** True when the displayed numbers did not come from a live fetch. */
  get isStale(): boolean {
    return this.status !== ProviderStatus.REFRESHED;
  }

  /** True when this provider cannot take part in orders right now. */
  get isUnusable(): boolean {
    return (
      this.status === ProviderStatus.UNAUTHENTICATED ||
      this.status === ProviderStatus.ERROR
    );
  }

  /** The payload the backend replays to fill in providers we can't reach. */
  toSnapshot() {
    return {
      provider: this.provider,
      holdings: this.holdings,
      cash: this.cash,
      profit_or_loss_v2: {
        dividends: this.dividends,
        appreciation: this.appreciation,
      },
      refreshed_at: this.refreshed_at,
    };
  }
}
