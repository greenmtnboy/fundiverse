import {
  configureDuckDBAssets,
  type DuckDBAssetUrls,
} from '@trilogy-data/trilogy-studio-components/connections'

import duckdbMvp from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url'
import duckdbMvpWorker from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url'
import duckdbEh from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url'
import duckdbEhWorker from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url'

const duckdbAssets: DuckDBAssetUrls = {
  mvp: {
    mainModule: duckdbMvp,
    mainWorker: duckdbMvpWorker,
  },
  eh: {
    mainModule: duckdbEh,
    mainWorker: duckdbEhWorker,
  },
}

configureDuckDBAssets(duckdbAssets)
