const BASE_URL = "http://localhost:5000";

export class FetchError extends Error {
  response: { status: number; data: any };

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = "FetchError";
    this.response = { status, data };
  }
}

async function handleResponse(
  res: Response,
): Promise<{ data: any; status: number }> {
  if (!res.ok) {
    let errorData: any = null;
    try {
      errorData = await res.json();
    } catch {}

    throw new FetchError(
      `Request failed with status ${res.status}`,
      res.status,
      errorData,
    );
  }

  let data: any = null;
  try {
    data = await res.json();
  } catch {}

  return { data, status: res.status };
}

async function get(path: string): Promise<{ data: any; status: number }> {
  const res = await fetch(`${BASE_URL}/${path}`, {
    method: "GET",
  });
  return handleResponse(res);
}

async function post(
  path: string,
  body?: unknown,
): Promise<{ data: any; status: number }> {
  const res = await fetch(`${BASE_URL}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handleResponse(res);
}

const desiredResponseCode = 200;

const maxAsyncMinutes = 10;

async function makeAsyncRequestInner(guid, startTime) {
  const currentTime = Date.now();
  if (currentTime - startTime >= maxAsyncMinutes * 60 * 1000) {
    throw new Error("Async request timed out after 10 minutes.");
  }

  const response = await get(`background_tasks/${guid}`);
  const { status } = response;
  if (status === desiredResponseCode) {
    return response;
  }

  await new Promise((resolve) => setTimeout(resolve, 500));
  return await makeAsyncRequestInner(guid, startTime);
}

export async function makeAsyncRequest(asyncApi, args) {
  const response = await post(`async_${asyncApi}`, args);
  const guid = response.data.guid;
  const startTime = Date.now();
  return await makeAsyncRequestInner(guid, startTime);
}

export const instance = { get, post, makeAsyncRequest };
