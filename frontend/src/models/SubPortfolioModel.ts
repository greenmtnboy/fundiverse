import PortfolioElementModel from "./PortfolioElementModel"; 
import CashModel from "./CashModel";
import { reactive } from 'vue';

export default class SubPortfolioModel {
    name: string;
    holdings:Array<PortfolioElementModel>;
    cash: CashModel;
    target_size: number;
    provider: string;
    loading:boolean;

    constructor({name, holdings, cash, target_size, provider}) {
        this.name = name;
        this.holdings = reactive(holdings);
        this.cash = new CashModel(cash);
        this.target_size = target_size;
        this.provider = provider;
        this.loading = false;
    }
} 