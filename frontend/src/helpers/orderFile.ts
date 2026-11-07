export interface UploadedOrder {
  ticker: string;
  side: "BUY" | "SELL";
  shares?: number;
  value?: number;
  /** per share limit; orders without one go at market */
  price?: number;
  broker?: string;
}

export interface ParsedOrders {
  orders: UploadedOrder[];
  /** one message per bad line; a file with any is not used at all */
  errors: string[];
}

const TICKER = /^[A-Z0-9][A-Z0-9.-]*$/;
const BROKERS = ["alpaca", "robinhood", "webull", "moomoo", "schwab", "etrade"];
// a comma outside double quotes
const COLUMN_SPLIT = /,(?=(?:[^"]*"[^"]*")*[^"]*$)/;

function columns(line: string): string[] {
  return line.split(COLUMN_SPLIT).map((x) => x.replace(/"/g, "").trim());
}

function amount(raw: string | undefined): number | undefined | null {
  if (!raw) {
    return undefined;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

/** Read orders from a CSV with a header row: side, ticker, either shares or
 * value, and optionally broker and a per share price. Other columns are
 * ignored. These become real orders, so a bad line rejects the file rather
 * than being skipped. */
export function parseOrderFile(text: string): ParsedOrders {
  const lines = text
    .replace(/^﻿/, "")
    .split(/\r?\n/)
    .map((line, index) => ({ line: line.trim(), number: index + 1 }))
    .filter(({ line }) => line && !line.startsWith("#"));
  if (!lines.length) {
    return { orders: [], errors: ["The file is empty."] };
  }
  const header = columns(lines[0].line).map((x) => x.toLowerCase());
  const missing = ["side", "ticker"].filter((x) => !header.includes(x));
  if (!header.includes("shares") && !header.includes("value")) {
    missing.push("shares or value");
  }
  if (missing.length) {
    return { orders: [], errors: [`Missing columns: ${missing.join(", ")}.`] };
  }

  const orders: UploadedOrder[] = [];
  const errors: string[] = [];
  for (const { line, number } of lines.slice(1)) {
    const cells = columns(line);
    const cell = (name: string) => cells[header.indexOf(name)];
    const side = cell("side")?.toUpperCase();
    const ticker = cell("ticker")?.toUpperCase();
    const shares = amount(cell("shares"));
    const value = amount(cell("value"));
    const price = amount(cell("price"));
    const broker = cell("broker")?.toLowerCase().replace(/[^a-z]/g, "");

    const problems: string[] = [];
    if (side !== "BUY" && side !== "SELL") {
      problems.push("side must be BUY or SELL");
    }
    if (!ticker || !TICKER.test(ticker)) {
      problems.push("bad ticker");
    }
    if (shares === null || value === null) {
      problems.push("shares and value must be positive numbers");
    } else if (!shares === !value) {
      problems.push("give either shares or value");
    }
    if (price === null) {
      problems.push("price must be a positive number");
    }
    if (broker && !BROKERS.includes(broker)) {
      problems.push(`unknown broker ${cell("broker")}`);
    }
    if (problems.length) {
      errors.push(`Line ${number}: ${problems.join("; ")}.`);
      continue;
    }
    orders.push({
      ticker: ticker!,
      side: side as UploadedOrder["side"],
      ...(shares ? { shares } : { value: value! }),
      ...(price ? { price } : {}),
      ...(broker ? { broker } : {}),
    });
  }
  if (!orders.length && !errors.length) {
    errors.push("The file has no orders.");
  }
  return errors.length ? { orders: [], errors } : { orders, errors };
}
