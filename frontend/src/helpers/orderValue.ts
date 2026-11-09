interface Money {
  value: number | string;
  currency: string;
}

interface Order {
  value?: Money | null;
  qty?: number | string | null;
  price?: Money | null;
  estimated_fee?: Money | null;
}

/**
 * Dollar value of an order: its value for dollar orders, or qty times the
 * planning price for unit orders. Null when a unit order has no price.
 */
export function orderValue(order: Order): Money | null {
  if (order.value) {
    return order.value;
  }
  if (order.qty && order.price) {
    return {
      value: Number(order.qty) * Number(order.price.value),
      currency: order.price.currency,
    };
  }
  return null;
}

export function totalOrderValue(orders: Order[]): number {
  return orders.reduce((total, order) => {
    const money = orderValue(order);
    return money ? total + Number(money.value) : total;
  }, 0);
}

/** Commissions the brokers are expected to charge, such as for OTC orders. */
export function totalOrderFees(orders: Order[]): number {
  return orders.reduce(
    (total, order) =>
      order.estimated_fee ? total + Number(order.estimated_fee.value) : total,
    0,
  );
}
