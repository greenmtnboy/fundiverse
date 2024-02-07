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
  profit_and_loss?: number;
  error?: string | null;

  constructor({
    name,
    holdings,
    cash,
    target_size,
    components,
    refreshed_at,
    profit_and_loss,
  }) {
    this.name = name;
    this.loading = false;
    this.holdings = holdings;
    this.cash = new CashModel(cash);
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
    this.profit_and_loss = profit_and_loss;
    this.error = null;
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
