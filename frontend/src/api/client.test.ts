import { fixtureResume } from "../features/dev/fixtureResume";
import { ApiError, apiGet, apiPost } from "./client";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function reply(status: number, body: string): Response {
  return new Response(body, { status, headers: { "Content-Type": "application/json" } });
}

test("returns the parsed body of a successful request", async () => {
  fetchMock.mockResolvedValue(reply(200, JSON.stringify({ status: "ok", compiler: "ok" })));

  const health = await apiGet("/api/v1/health");

  expect(health).toEqual({ status: "ok", compiler: "ok" });
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/health", undefined);
});

test("turns the backend error envelope into an ApiError", async () => {
  const envelope = {
    error: { code: "template_not_found", message: "No such template.", details: { id: "x" } },
  };
  fetchMock.mockResolvedValue(reply(404, JSON.stringify(envelope)));

  const error = await apiGet("/api/v1/templates").catch((e: unknown) => e);

  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({
    status: 404,
    code: "template_not_found",
    message: "No such template.",
    details: { id: "x" },
  });
});

test("an error reply that is not the envelope is an unexpected_response", async () => {
  fetchMock.mockResolvedValue(reply(502, "<html>Bad gateway</html>"));

  const error = await apiGet("/api/v1/health").catch((e: unknown) => e);

  expect(error).toMatchObject({ status: 502, code: "unexpected_response" });
});

test("JSON without the envelope shape is an unexpected_response too", async () => {
  fetchMock.mockResolvedValue(reply(500, JSON.stringify({ oops: true })));

  const error = await apiGet("/api/v1/health").catch((e: unknown) => e);

  expect(error).toMatchObject({ status: 500, code: "unexpected_response" });
});

test("a success reply that is not JSON is an unexpected_response", async () => {
  fetchMock.mockResolvedValue(reply(200, "not json"));

  const error = await apiGet("/api/v1/health").catch((e: unknown) => e);

  expect(error).toMatchObject({ status: 200, code: "unexpected_response" });
});

test("a request that never reaches the server is a network_error", async () => {
  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

  const error = await apiGet("/api/v1/health").catch((e: unknown) => e);

  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 0, code: "network_error" });
});

const renderBody = { resume: fixtureResume, template_id: "dense-single" };

test("apiPost sends the body as JSON and returns the parsed reply", async () => {
  const rendered = {
    pdf_hash: "p",
    tex_hash: "t",
    page_count: 1,
    last_page_fill: 0.5,
    text_map: {},
  };
  fetchMock.mockResolvedValue(reply(200, JSON.stringify(rendered)));

  const result = await apiPost("/api/v1/dev/render", renderBody);

  expect(result).toEqual(rendered);
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/dev/render", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(renderBody),
  });
});

test("apiPost turns an error envelope into an ApiError", async () => {
  const envelope = {
    error: {
      code: "compile_failed",
      message: "The resume did not compile.",
      details: { log_tail: "x" },
    },
  };
  fetchMock.mockResolvedValue(reply(422, JSON.stringify(envelope)));

  const error = await apiPost("/api/v1/dev/render", renderBody).catch((e: unknown) => e);

  expect(error).toMatchObject({ status: 422, code: "compile_failed", details: { log_tail: "x" } });
});
