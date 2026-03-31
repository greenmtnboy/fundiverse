import store from "/src/store";
import exceptions from "./exceptions";
import { ipcRenderer } from "electron";

// must match port in backend\src\main.py
const BASE_URL = "http://localhost:3042";

let authHeader: string | null = null;

// Listen for the shared-variable event
if (ipcRenderer) {
  ipcRenderer.on("api-key", (_, API_KEY: string) => {
    authHeader = `Bearer ${API_KEY}`;
  });
}

export class FetchError extends Error {
  response: { status: number; data: any };
  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = "FetchError";
    this.response = { status, data };
  }
}

export function isFetchError(error: unknown): error is FetchError {
  return error instanceof FetchError;
}

function buildHeaders(
  method: "GET" | "POST",
  extra?: Record<string, string>,
): Record<string, string> {
  const headers: Record<string, string> = { ...extra };
  if (authHeader) headers["Authorization"] = authHeader;
  if (method === "POST") headers["Content-Type"] = "application/json";
  return headers;
}

async function handleResponse(
  res: Response,
  responseType: "blob" | "json" = "json",
): Promise<{ data: any; status: number }> {
  if (!res.ok) {
    let errorData: any = null;
    try {
      errorData = await res.json();
    } catch {}

    if (res.status === 401) {
      store.getters.providers.forEach((provider: string) => {
        store.dispatch("probeLogin", { provider });
      });
      throw new exceptions.auth("User is not authenticated");
    }
    if (res.status === 303) {
      throw new exceptions.auth_external_login(errorData?.detail);
    }
    if (res.status === 412) {
      throw new exceptions.auth_extra("Extra authentication factor required");
    }
    throw new FetchError(
      `Request failed with status ${res.status}`,
      res.status,
      errorData,
    );
  }

  let data: any = null;
  try {
    data = responseType === "blob" ? await res.blob() : await res.json();
  } catch {}

  return { data, status: res.status };
}

interface RequestOptions {
  responseType?: "blob" | "json";
  headers?: Record<string, string>;
}

async function get(
  path: string,
  options: RequestOptions = {},
): Promise<{ data: any; status: number }> {
  const res = await fetch(`${BASE_URL}/${path}`, {
    method: "GET",
    headers: buildHeaders("GET", options.headers),
  });
  return handleResponse(res, options.responseType ?? "json");
}

async function post(
  path: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<{ data: any; status: number }> {
  const res = await fetch(`${BASE_URL}/${path}`, {
    method: "POST",
    headers: buildHeaders("POST", options.headers),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handleResponse(res, options.responseType ?? "json");
}

const maxAsyncMinutes = 10;
const desiredResponseCode = 200;

async function makeAsyncRequestInner(
  guid: string,
  startTime: number,
): Promise<{ data: any; status: number } | undefined> {
  if (Date.now() - startTime >= maxAsyncMinutes * 60 * 1000) {
    console.log("Loop has been running for more than 10 minutes. Breaking the loop.");
    return;
  }
  const response = await get(`background_tasks/${guid}`);
  if (response.status === desiredResponseCode) {
    return response;
  }
  await new Promise((resolve) => setTimeout(resolve, 500));
  return makeAsyncRequestInner(guid, startTime);
}

export async function makeAsyncRequest(asyncApi: string, args: unknown) {
  const response = await post(`async_${asyncApi}`, args);
  const guid = response.data.guid;
  return makeAsyncRequestInner(guid, Date.now());
}

const instance = { get, post, makeAsyncRequest };

export default instance;
