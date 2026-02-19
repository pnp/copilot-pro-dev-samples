import express from "express";
import cors from "cors";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpServer } from "./mcp-server.js";

const PORT = parseInt(process.env.PORT ?? "3001", 10);

const app = express();

app.use(cors({ origin: "*" }));
app.use(express.json());

// ── Health check ───────────────────────────────────────────────────────
app.get("/", (_req, res) => {
  res.json({ name: "zava-insurance-mcp", status: "ok" });
});

// ── MCP endpoint — Streamable HTTP (stateless) ────────────────────────
app.all("/mcp", async (req, res) => {
  try {
    const server = createMcpServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless
      enableJsonResponse: true,      // avoid 30s SSE timeout
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (err) {
    console.error("MCP error:", err);
    if (!res.headersSent) {
      res.status(500).json({ error: "Internal server error" });
    }
  }
});

// ── Start ──────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`🚀 Zava Insurance MCP server running at http://localhost:${PORT}`);
  console.log(`   MCP endpoint: http://localhost:${PORT}/mcp`);
});
