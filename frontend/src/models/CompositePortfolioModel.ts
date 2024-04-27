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
  target_size: number;
  keys: Array<string>;
  components: Array<SubPortfolioModel>;
  type?: string;
  refreshed_at: number;
  profit_and_loss?: CashModel;
  dividends: CashModel;
  appreciation: CashModel;
  error?: string | null;

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
  }) {
    this.name = name;
    this.loading = false;
    this.holdings = holdings;
    this.cash = new CashModel(cash);
    this.target_size = target_size;
    const scomponents: Array<any> = components as Array<any>;
    this.keys = reactive(
      Object.entries(scomponents).map(([_, component]) => component.provider)
    );
    this.components = reactive(
      Object.entries(scomponents).map(
        ([_, component]) => new SubPortfolioModel(component)
      )
    );
    this.refreshed_at = refreshed_at;
    if (profit_or_loss && profit_or_loss.value) {
      this.profit_and_loss = new CashModel(profit_or_loss);
    } else {
      this.profit_and_loss = new CashModel({
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

  get totalValue() {
    return Number(
      this.holdings.reduce(
        (sum, holding) =>
          BigInt(
            sum +
              BigInt(Math.floor(parseFloat(holding.value.value || "0") * 10000))
          ) >> BigInt(0),
        BigInt(0)
      ) / BigInt(10000)
    );
  }

  valueInIndex(index: TargetPortfolioModel) {
    if (!index) {
      return [];
    }
    const indexTickers = index.holdings.reduce(
      (set, holding) => set.add(holding.ticker),
      new Set()
    );
    return Number(
      this.holdings
        .filter((element) => indexTickers.has(element.ticker))
        .reduce(
          (sum, holding) =>
            BigInt(
              sum +
                BigInt(
                  Math.floor(parseFloat(holding.value.value || "0") * 10000)
                )
            ) >> BigInt(0),
          BigInt(0)
        ) / BigInt(10000)
    );
  }
}
