import PortfolioElementModel from "./PortfolioElementModel"; 
import CashModel from "./CashModel";
import SubPortfolioModel from "./SubPortfolioModel"

export default class CompositePortfolioModel {
    name: string;
    loading:boolean;
    holdings:Array<PortfolioElementModel>;
    cash: CashModel;
    target_size: number;
    keys: Array<string>;
    components: Array<SubPortfolioModel>;
    type?: string;

    constructor({name, holdings, cash, target_size, components}) {
        this.name = name;
        this.loading=false;
        this.holdings = holdings;
        this.cash = new CashModel(cash);
        this.target_size = target_size;
        const scomponents:Array<any> =components as Array<any>
        this.keys = Object.entries(scomponents).map(([key, component]) => component.provider)
        this.components = Object.entries(scomponents).map(([key, component]) => new SubPortfolioModel(component))
        
    }
} 