/**
 * Main ChatGPT-like Sales Analytics Assistant Server
 * Integrates with LangGraph flows for sales analysis and forecasting
 */

import express from "express";
import multer from "multer";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { v4 as uuidv4 } from "uuid";
import dotenv from "dotenv";
import path from "path";
import { spawn } from "child_process";

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configure file upload
const upload = multer({
  dest: "uploads/",
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB max
  fileFilter: (req, file, cb) => {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error("Only JPEG, PNG, and WebP images allowed"));
    }
  },
});

// Enhanced session store for analytics context
interface AnalyticsSession {
  id: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: number;
    metadata?: {
      intent?: string;
      toolsUsed?: string[];
      dataContext?: any;
    };
  }>;
  lastAnalyzedProduct?: {
    id: string;
    name: string;
    type: string;
    lastMetrics?: any;
  };
  lastTimeframe?: string;
  conversationContext?: {
    currentAnalysisType?: string;
    pendingComparisons?: any[];
    chartPreferences?: any;
  };
  createdAt: number;
  lastUpdated: number;
}

const sessions = new Map<string, AnalyticsSession>();
const SESSION_TTL = parseInt(process.env.SESSION_TTL_SECONDS || "3600") * 1000;

// Rate limiting
const chatRateLimit = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 50, // 50 requests per minute
  message: {
    error: "Too many requests, please try again later",
    retryAfter: 60,
  },
});

// Security middleware
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", "data:", "https:"],
      },
    },
  })
);

app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "http://localhost:3001",
    credentials: true,
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Session management for analytics context
function getSession(sessionId: string): AnalyticsSession {
  const session = sessions.get(sessionId);
  if (!session || Date.now() - session.lastUpdated > SESSION_TTL) {
    const newSession: AnalyticsSession = {
      id: sessionId,
      messages: [],
      createdAt: Date.now(),
      lastUpdated: Date.now(),
    };
    sessions.set(sessionId, newSession);
    return newSession;
  }
  return session;
}

function updateSession(
  sessionId: string,
  role: string,
  content: string,
  metadata?: any
) {
  const session = getSession(sessionId);
  session.messages.push({
    role,
    content,
    timestamp: Date.now(),
    metadata,
  });

  // Keep last 20 messages for better context
  const maxMessages = parseInt(process.env.MAX_CONVERSATION_HISTORY || "20");
  session.messages = session.messages.slice(-maxMessages);
  session.lastUpdated = Date.now();

  // Update session context from metadata
  if (metadata?.dataContext) {
    if (metadata.dataContext.lastAnalyzedProduct) {
      session.lastAnalyzedProduct = metadata.dataContext.lastAnalyzedProduct;
    }
    if (metadata.dataContext.lastTimeframe) {
      session.lastTimeframe = metadata.dataContext.lastTimeframe;
    }
  }
}

// LangGraph integration
async function callLangGraphFlow(input: any): Promise<any> {
  return new Promise((resolve, reject) => {
    try {
      // Call the Python LangGraph runner
      const pythonPath = path.join(__dirname, "../venv/bin/python");
      const scriptPath = path.join(__dirname, "../langgraph/runner.py");

      const inputData = JSON.stringify({
        message: input.message,
        session_id: input.session_id,
        method: input.method, // Add method parameter for ReAct/Intent selection
        context: input.context,
      });

      const { spawn } = require("child_process");
      const pythonProcess = spawn(pythonPath, [scriptPath], {
        stdio: ["pipe", "pipe", "pipe"],
        cwd: path.join(__dirname, ".."),
      });

      let output = "";
      let errorOutput = "";

      pythonProcess.stdin.write(inputData);
      pythonProcess.stdin.end();

      pythonProcess.stdout.on("data", (data: Buffer) => {
        output += data.toString();
      });

      pythonProcess.stderr.on("data", (data: Buffer) => {
        errorOutput += data.toString();
      });

      pythonProcess.on("close", (code: number) => {
        if (code === 0) {
          try {
            const result = JSON.parse(output);
            // Debug logging to see what we get from Python
            console.log("Python result:", JSON.stringify(result, null, 2));
            resolve(result);
          } catch (parseError) {
            console.error("Failed to parse Python output:", output);
            resolve({
              success: false,
              response:
                "I encountered an error processing your request. Please ensure the backend API is running.",
              intent: "error",
              tool_results: [],
              session_context: {},
            });
          }
        } else {
          console.error("Python process failed:", errorOutput);
          resolve({
            success: false,
            response:
              "I'm unable to connect to the backend server. Please ensure the inventory API is running on port 8000.",
            intent: "error",
            tool_results: [],
            session_context: {},
          });
        }
      });

      pythonProcess.on("error", (error: Error) => {
        console.error("Failed to start Python process:", error);
        resolve({
          success: false,
          response:
            "I'm experiencing technical difficulties. Please try again later.",
          intent: "error",
          tool_results: [],
          session_context: {},
        });
      });
    } catch (error) {
      console.error("Error in callLangGraphFlow:", error);
      resolve({
        success: false,
        response:
          "I'm experiencing technical difficulties. Please try again later.",
        intent: "error",
        tool_results: [],
        session_context: {},
      });
    }
  });
}

// Mock functions removed - now using real LangGraph integration

// Main chat endpoint with streaming support
app.post("/chat", chatRateLimit, upload.single("image"), async (req, res) => {
  try {
    const {
      message,
      session_id = uuidv4(),
      stream = false,
      method = "auto",
    } = req.body;
    const imageFile = req.file;

    if (!message || typeof message !== "string") {
      return res.status(400).json({
        error: "Message is required and must be a string",
      });
    }

    // Get session context
    const session = getSession(session_id);

    // Prepare input for LangGraph flow
    const flowInput = {
      message,
      session_id,
      method, // Add method parameter for ReAct/Intent/Auto selection
      image: imageFile?.path,
      context: {
        conversationHistory: session.messages.slice(-10),
        lastAnalyzedProduct: session.lastAnalyzedProduct,
        lastTimeframe: session.lastTimeframe,
        conversationContext: session.conversationContext,
      },
    };

    if (stream && process.env.ENABLE_STREAMING === "true") {
      // Set up streaming response
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");
      res.setHeader("Access-Control-Allow-Origin", "*");

      try {
        // Execute LangGraph flow
        const flowResult = await callLangGraphFlow(flowInput);

        if (flowResult.success) {
          // Stream response chunks
          const response = flowResult.response;
          const words = response.split(" ");

          for (let i = 0; i < words.length; i++) {
            const chunk = words.slice(0, i + 1).join(" ");
            res.write(
              `data: ${JSON.stringify({
                chunk: chunk,
                done: false,
                progress: (i + 1) / words.length,
              })}\n\n`
            );

            // Simulate typing delay
            await new Promise((resolve) => setTimeout(resolve, 50));
          }

          // Send completion with ReAct support
          const completionData: any = {
            done: true,
            session_id,
            metadata: {
              intent: flowResult.intent,
              toolsUsed:
                flowResult.tool_results?.map((tr: any) => tr.tool) || [],
            },
          };

          // Add ReAct-specific fields if present
          if (flowResult.method) {
            completionData.method = flowResult.method;
          }
          if (flowResult.reasoning_trace) {
            completionData.reasoning_trace = flowResult.reasoning_trace;
          }
          if (flowResult.iterations) {
            completionData.iterations = flowResult.iterations;
          }
          if (flowResult.tools_used) {
            completionData.tools_used = flowResult.tools_used;
          }

          res.write(`data: ${JSON.stringify(completionData)}\n\n`);

          // Update session
          updateSession(session_id, "user", message);
          updateSession(session_id, "assistant", flowResult.response, {
            intent: flowResult.intent,
            toolsUsed: flowResult.tool_results?.map((tr: any) => tr.tool) || [],
            dataContext: flowResult.session_context,
          });
        } else {
          res.write(
            `data: ${JSON.stringify({
              error: true,
              message: flowResult.response,
              done: true,
            })}\n\n`
          );
        }

        res.end();
        return;
      } catch (error) {
        res.write(
          `data: ${JSON.stringify({
            error: true,
            message: "Stream processing failed",
            done: true,
          })}\n\n`
        );
        res.end();
        return;
      }
    } else {
      // Regular JSON response
      const flowResult = await callLangGraphFlow(flowInput);

      // Update session with metadata
      updateSession(session_id, "user", message);
      updateSession(session_id, "assistant", flowResult.response, {
        intent: flowResult.intent,
        toolsUsed: flowResult.tool_results?.map((tr: any) => tr.tool) || [],
        dataContext: flowResult.session_context,
      });

      // Build response object with ReAct support
      const response: any = {
        message: flowResult.response,
        session_id,
        metadata: {
          intent: flowResult.intent,
          toolsUsed: flowResult.tool_results?.map((tr: any) => tr.tool) || [],
          hasChartData: flowResult.tool_results?.some(
            (tr: any) => tr.tool === "generate_chart_data"
          ),
          processingTime: Date.now() - Date.now(), // Will be calculated properly
        },
      };

      // Add ReAct-specific fields if present
      if (flowResult.method) {
        response.method = flowResult.method;
      }
      if (flowResult.reasoning_trace) {
        response.reasoning_trace = flowResult.reasoning_trace;
      }
      if (flowResult.iterations) {
        response.iterations = flowResult.iterations;
      }
      if (flowResult.tools_used) {
        response.tools_used = flowResult.tools_used;
      }

      res.json(response);
      return;
    }
  } catch (error) {
    console.error("Chat error:", error);
    res.status(500).json({
      error: "Internal server error",
      message: "Please try again later",
    });
    return;
  }
});

// Get conversation history
app.get("/chat/:session_id/history", (req, res) => {
  try {
    const session = sessions.get(req.params.session_id);
    if (!session) {
      return res.status(404).json({ error: "Session not found" });
    }

    res.json({
      session_id: req.params.session_id,
      messages: session.messages,
      context: {
        lastAnalyzedProduct: session.lastAnalyzedProduct,
        conversationContext: session.conversationContext,
        lastTimeframe: session.lastTimeframe,
      },
      metadata: {
        messageCount: session.messages.length,
        sessionAge: Date.now() - session.createdAt,
        lastActivity: Date.now() - session.lastUpdated,
      },
    });
    return;
  } catch (error) {
    console.error("History retrieval error:", error);
    res.status(500).json({ error: "Failed to retrieve conversation history" });
    return;
  }
});

// Clear session
app.delete("/chat/:session_id", (req, res) => {
  try {
    const sessionId = req.params.session_id;
    const deleted = sessions.delete(sessionId);

    res.json({
      success: deleted,
      message: deleted ? "Session cleared successfully" : "Session not found",
    });
  } catch (error) {
    console.error("Session deletion error:", error);
    res.status(500).json({ error: "Failed to clear session" });
  }
});

// Health check with detailed status
app.get("/health", (req, res) => {
  const now = Date.now();
  const activeSessions = Array.from(sessions.values()).filter(
    (session) => now - session.lastUpdated < SESSION_TTL
  ).length;

  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    server: {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      activeSessions,
      totalSessions: sessions.size,
    },
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      streamingEnabled: process.env.ENABLE_STREAMING === "true",
    },
    features: {
      langraph: "enabled",
      openai: !!process.env.OPENAI_API_KEY,
      streaming: process.env.ENABLE_STREAMING === "true",
      redis: !!process.env.REDIS_URL,
    },
  });
});

// Analytics endpoint for debugging
app.get("/analytics/sessions", (req, res) => {
  if (process.env.NODE_ENV !== "development") {
    return res.status(403).json({ error: "Only available in development" });
  }

  const sessionSummary = Array.from(sessions.entries()).map(
    ([id, session]) => ({
      id: id.substring(0, 8) + "...",
      messageCount: session.messages.length,
      lastActivity: new Date(session.lastUpdated).toISOString(),
      lastAnalyzedProduct: session.lastAnalyzedProduct?.name,
      age: Date.now() - session.createdAt,
    })
  );

  res.json({
    totalSessions: sessions.size,
    activeSessions: sessionSummary.filter((s) => s.age < SESSION_TTL).length,
    sessions: sessionSummary,
  });
  return;
});

// Cleanup expired sessions
setInterval(() => {
  const now = Date.now();
  let cleanedCount = 0;

  for (const [sessionId, session] of sessions.entries()) {
    if (now - session.lastUpdated > SESSION_TTL) {
      sessions.delete(sessionId);
      cleanedCount++;
    }
  }

  if (cleanedCount > 0) {
    console.log(`🧹 Cleaned up ${cleanedCount} expired sessions`);
  }
}, 5 * 60 * 1000); // Every 5 minutes

// Error handling middleware
app.use(
  (
    error: any,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    console.error("Unhandled error:", error);

    if (error instanceof multer.MulterError) {
      if (error.code === "LIMIT_FILE_SIZE") {
        return res
          .status(400)
          .json({ error: "File too large. Maximum size is 10MB." });
      }
      return res
        .status(400)
        .json({ error: "File upload error: " + error.message });
    }

    res.status(500).json({
      error: "Internal server error",
      message:
        process.env.NODE_ENV === "development"
          ? error.message
          : "Please try again later",
    });
    return;
  }
);

// 404 handler
app.use("*", (req, res) => {
  res.status(404).json({
    error: "Endpoint not found",
    availableEndpoints: [
      "POST /chat - Main chat interface",
      "GET /chat/:session_id/history - Get conversation history",
      "DELETE /chat/:session_id - Clear session",
      "GET /health - Health check",
      "GET /analytics/sessions - Session analytics (dev only)",
    ],
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Sales Analytics Assistant Server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`💬 Chat endpoint: http://localhost:${PORT}/chat`);
  console.log(`🔧 Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(
    `⚡ Streaming: ${
      process.env.ENABLE_STREAMING === "true" ? "enabled" : "disabled"
    }`
  );

  if (!process.env.OPENAI_API_KEY) {
    console.warn("⚠️  OPENAI_API_KEY not set - AI responses will not work");
  }

  if (!process.env.BASE_URL) {
    console.warn("⚠️  BASE_URL not set - inventory API calls will fail");
  }

  console.log("🎯 Ready for sales analytics conversations!");
});

// Graceful shutdown
process.on("SIGTERM", () => {
  console.log("🛑 SIGTERM received, shutting down gracefully");

  // Clear all sessions
  sessions.clear();

  process.exit(0);
});

process.on("SIGINT", () => {
  console.log("🛑 SIGINT received, shutting down gracefully");

  // Clear all sessions
  sessions.clear();

  process.exit(0);
});

export default app;
