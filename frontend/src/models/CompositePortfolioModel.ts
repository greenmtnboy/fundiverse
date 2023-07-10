import PortfolioElementModel from "./PortfolioElementModel"; 
import CashModel from "./CashModel";
import PortfolioModel from "./PortfolioModel"

export default class CompositePortfolioModel {
    name: string;
    holdings:Array<PortfolioElementModel>;
    cash: CashModel;
    target_size: number;
    keys: Array<string>;
    components: Array<PortfolioModel>;

    constructor({name, holdings, cash, target_size, components}) {
        this.name = name;
        this.holdings = holdings;
        this.cash = new CashModel(cash);
        this.target_size = target_size;
        if (components) {
            this.keys = Object.entries(components).map(([key, component]) => key) 
            this.components =  Object.entries(components).map(([key]) => new CompositePortfolioModel(components[key]))
        }
        else {
            this.keys = [];
            this.components = [];
        }
        // []; //components.map((component) => new PortfolioModel(component));
    }
} 