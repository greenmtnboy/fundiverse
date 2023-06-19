import PortfolioElementModel from "./PortfolioElementModel"; 

export default class PortfolioModel {
    holdings:Array<PortfolioElementModel>;

    constructor(holdings) {
        this.holdings = holdings
    }
} 