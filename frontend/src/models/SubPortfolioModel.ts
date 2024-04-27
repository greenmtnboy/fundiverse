import PortfolioElementModel from "./PortfolioElementModel";
import CashModel from "./CashModel";
import { reactive } from "vue";

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

  constructor({
    name,
    holdings,
    cash,
    target_size,
    provider,
    profit_or_loss_v2,
    profit_or_loss,
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
  }
}
