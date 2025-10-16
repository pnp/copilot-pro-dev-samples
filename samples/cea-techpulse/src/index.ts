// Import required packages
import {
  AuthConfiguration,
  authorizeJWT,
  loadAuthConfigFromEnv,
  Request,
} from "@microsoft/agents-hosting";
import express, { Response } from "express";
import path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// This bot's adapter
import adapter from "./adapter.js";

// This bot's main dialog.
import { agentApp } from "./agent.js";

// Create authentication configuration
const authConfig: AuthConfiguration = loadAuthConfigFromEnv();

// Create express application.
const expressApp = express();

// Add request logging middleware
expressApp.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

expressApp.use(express.json());
expressApp.use(authorizeJWT(authConfig));

const port = process.env.port || process.env.PORT || 3978;


// Add a health check endpoint
expressApp.get('/health', (req, res) => {
  console.log('Health check requested');
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
});



const server = expressApp.listen(process.env.port || process.env.PORT || 3978, () => {
  console.log(`\nAgent started, ${expressApp.name} listening to`, server.address());
});

// Listen for incoming requests.
expressApp.post("/api/messages", async (req: Request, res: Response) => {
  console.log('Message received on /api/messages endpoint');
  console.log('Request body:', req.body);
  
  try {
    await adapter.process(req, res, async (context) => {
      console.log('Processing message through adapter');
      await agentApp.run(context);
    });
  } catch (error) {
    console.error('Error processing message:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down gracefully...');
  server.close(() => {
    console.log('HTTP server closed.');
    process.exit(0);
  });
});

process.on('SIGINT', async () => {
  console.log('Shutting down gracefully...');
  server.close(() => {
    console.log('HTTP server closed.');
    process.exit(0);
  });
});