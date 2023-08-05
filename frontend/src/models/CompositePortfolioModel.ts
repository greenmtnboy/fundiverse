import PortfolioElementModel from "./PortfolioElementModel"; 
import CashModel from "./CashModel";
import SubPortfolioModel from "./SubPortfolioModel"
import { reactive } from 'vue';

export default class CompositePortfolioModel {
    name: string;
    loading:boolean;
    holdings:Array<PortfolioElementModel>;
    cash: CashModel;
    target_size: number;
    keys: Array<string>;
    components: Array<SubPortfolioModel>;
    type?: string;
    refreshed_at: number;

    constructor({name, holdings, cash, target_size, components, refreshed_at}) {
        this.name = name;
        this.loading=false;
        this.holdings = holdings;
        this.cash = new CashModel(cash);
        this.target_size = target_size;
        const scomponents:Array<any> = components as Array<any>
        this.keys = reactive(Object.entries(scomponents).map(([key, component]) => component.provider))
        this.components = reactive(Object.entries(scomponents).map(([key, component]) => new SubPortfolioModel(component)))
        this.refreshed_at = refreshed_at
    }
    
} 