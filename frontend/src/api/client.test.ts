import { ApiError, apiGet } from "./client";

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
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/health");
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
