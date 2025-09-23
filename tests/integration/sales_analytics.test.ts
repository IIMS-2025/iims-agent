/**
 * Integration tests for sales analytics conversations
 */

import request from "supertest";
import app from "../../src/index";

describe("Sales Analytics Chat Integration", () => {
  let sessionId: string;

  beforeEach(() => {
    sessionId = `test_${Date.now()}`;
  });

  describe("Sales Trend Analysis", () => {
    it("should analyze sales trends for last month", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Show me sales trends for last month",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body).toHaveProperty("message");
      expect(response.body).toHaveProperty("session_id");
      expect(response.body.message).toContain("📈");
      expect(response.body.metadata.intent).toBe("analyze_sales_trends");
    });

    it("should handle product-specific sales analysis", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "How is Kerala Burger performing this month?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/kerala burger/i);
      expect(response.body.message).toMatch(/revenue|₹|performance/);
    });
  });

  describe("Sales Forecasting", () => {
    it("should generate sales forecasts", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Predict Kerala Burger sales for next 30 days",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toContain("🔮");
      expect(response.body.message).toMatch(/predict|forecast/i);
      expect(response.body.message).toMatch(/₹.*confidence/);
      expect(response.body.metadata.intent).toBe("forecast_sales");
    });

    it("should include inventory implications in forecasts", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "What will our inventory needs be next month?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/inventory|stock|need/i);
    });
  });

  describe("Product Performance Analysis", () => {
    it("should rank product performance", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Which menu items are performing best this quarter?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toContain("🏆");
      expect(response.body.message).toMatch(/top|best|perform/i);
      expect(response.body.metadata.intent).toBe("analyze_product_performance");
    });

    it("should identify underperforming products", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Show me worst performing products",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(
        /underperform|worst|bottom|needs attention/i
      );
    });
  });

  describe("Period Comparisons", () => {
    it("should compare revenue between periods", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Compare this month revenue vs last month",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toContain("📊");
      expect(response.body.message).toMatch(/vs|compare|%/);
      expect(response.body.metadata.intent).toBe("compare_periods");
    });
  });

  describe("Follow-up Context", () => {
    it("should handle follow-up questions using session context", async () => {
      // First message
      await request(app)
        .post("/chat")
        .send({
          message: "Show me Kerala Burger performance",
          session_id: sessionId,
        })
        .expect(200);

      // Follow-up message
      const response = await request(app)
        .post("/chat")
        .send({
          message: "What about the forecast for that product?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/forecast|predict/i);
      expect(response.body.message).toMatch(/kerala burger/i);
    });
  });

  describe("Help and Capabilities", () => {
    it("should provide help information", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "What can you help me with?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toContain("💡");
      expect(response.body.message).toMatch(/help|analyze|forecast/i);
      expect(response.body.metadata.intent).toBe("help");
    });
  });

  describe("Session Management", () => {
    it("should retrieve conversation history", async () => {
      // Send a few messages
      await request(app).post("/chat").send({
        message: "Show me sales trends",
        session_id: sessionId,
      });

      await request(app).post("/chat").send({
        message: "What about forecasts?",
        session_id: sessionId,
      });

      // Get history
      const response = await request(app)
        .get(`/chat/${sessionId}/history`)
        .expect(200);

      expect(response.body).toHaveProperty("messages");
      expect(response.body.messages).toHaveLength(4); // 2 user + 2 assistant
      expect(response.body).toHaveProperty("context");
    });

    it("should clear session data", async () => {
      // Send a message first
      await request(app).post("/chat").send({
        message: "Test message",
        session_id: sessionId,
      });

      // Clear session
      const response = await request(app)
        .delete(`/chat/${sessionId}`)
        .expect(200);

      expect(response.body.success).toBe(true);

      // Verify session is cleared
      const historyResponse = await request(app)
        .get(`/chat/${sessionId}/history`)
        .expect(404);
    });
  });

  describe("Error Handling", () => {
    it("should handle invalid input gracefully", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          // Missing message
          session_id: sessionId,
        })
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should handle empty messages", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "",
          session_id: sessionId,
        })
        .expect(400);

      expect(response.body.error).toMatch(/message.*required/i);
    });
  });
});
