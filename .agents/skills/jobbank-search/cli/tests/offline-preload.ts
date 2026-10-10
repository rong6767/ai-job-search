// Load this in CLI test subprocesses before the production entry point. Parent
// process fetch mocks do not carry over to Bun.spawn, so every child needs its
// own network guard. Reaching this sentinel proves valid arguments got through
// validation without querying a real job portal.
globalThis.fetch = (async () => {
  throw new Error("OFFLINE_TEST_NETWORK_BLOCKED: CLI tests must mock portal requests")
}) as typeof fetch
