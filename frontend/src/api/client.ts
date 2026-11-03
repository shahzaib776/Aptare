import type { paths } from "./schema";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, code: string, message: string, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type GetPath = {
  [P in keyof paths]: paths[P] extends { get: object } ? P : never;
}[keyof paths];

type JsonBody<Operation> = Operation extends {
  responses: { 200: { content: { "application/json": infer Body } } };
}
  ? Body
  : never;

type GetResponse<P extends GetPath> = paths[P] extends { get: infer Operation }
  ? JsonBody<Operation>
  : never;

/** GET one of the API's routes; the response type comes from the generated schema. */
export async function apiGet<P extends GetPath>(path: P): Promise<GetResponse<P>> {
  // The cast trusts the server to match the schema it generated; nothing can check it here.
  return (await request(path)) as GetResponse<P>;
}

type PostPath = {
  [P in keyof paths]: paths[P] extends { post: object } ? P : never;
}[keyof paths];

type PostBody<P extends PostPath> = paths[P] extends {
  post: { requestBody: { content: { "application/json": infer Body } } };
}
  ? Body
  : never;

type PostResponse<P extends PostPath> = paths[P] extends { post: infer Operation }
  ? JsonBody<Operation>
  : never;

/** POST a JSON body to one of the API's routes; both body and reply are typed from the schema. */
export async function apiPost<P extends PostPath>(
  path: P,
  body: PostBody<P>,
): Promise<PostResponse<P>> {
  const init = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
  return (await request(path, init)) as PostResponse<P>;
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError(0, "network_error", "Cannot reach the server.");
  }

  const body = await readJson(response);
  if (response.ok) {
    if (body === undefined) throw unexpected(response.status);
    return body;
  }

  const error = envelopeOf(body);
  if (error === undefined) throw unexpected(response.status);
  throw new ApiError(response.status, error.code, error.message, error.details);
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return JSON.parse(await response.text());
  } catch {
    return undefined;
  }
}

function unexpected(status: number): ApiError {
  return new ApiError(status, "unexpected_response", "The server sent a reply we cannot read.");
}

/** The backend's error shape: {"error": {"code", "message", "details"}}. */
function envelopeOf(
  body: unknown,
): { code: string; message: string; details: unknown } | undefined {
  if (typeof body !== "object" || body === null || !("error" in body)) return undefined;
  const { error } = body;
  if (typeof error !== "object" || error === null) return undefined;
  const fields = error as Record<string, unknown>;
  if (typeof fields.code !== "string" || typeof fields.message !== "string") return undefined;
  return { code: fields.code, message: fields.message, details: fields.details ?? null };
}
