export interface ParsedExclusions {
  tickers: string[];
  /** lines whose first column could not be a ticker, as they appeared */
  invalid: string[];
}

// covers home-listing tickers such as ESSITY-B.ST as well as US ones
const TICKER = /^[A-Z0-9][A-Z0-9.-]*$/;
const HEADERS = new Set(["TICKER", "SYMBOL"]);

/** Read tickers from a text or CSV file: the first column of each line, with
 * an optional header row. Blank lines and # comments are skipped. */
export function parseExclusionFile(text: string): ParsedExclusions {
  const tickers = new Set<string>();
  const invalid: string[] = [];
  let seenRow = false;
  for (const raw of text.replace(/^﻿/, "").split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const value = line
      .split(/[,;\t]/)[0]
      .replace(/"/g, "")
      .trim()
      .toUpperCase();
    const isHeader = !seenRow && HEADERS.has(value);
    seenRow = true;
    if (isHeader) {
      continue;
    }
    if (TICKER.test(value)) {
      tickers.add(value);
    } else {
      invalid.push(line);
    }
  }
  return { tickers: Array.from(tickers), invalid };
}
