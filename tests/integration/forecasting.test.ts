/**
 * Integration tests for sales forecasting functionality
 */

import request from "supertest";
import app from "../../src/index";

describe("Sales Forecasting Integration", () => {
  let sessionId: string;

  beforeEach(() => {
    sessionId = `forecast_test_${Date.now()}`;
  });

  describe("Sales Forecasting", () => {
    it("should generate 30-day sales forecasts", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Predict sales for next 30 days",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toContain("🔮");
      expect(response.body.message).toMatch(/predict|forecast/i);
      expect(response.body.message).toMatch(/30|month/i);
      expect(response.body.metadata.intent).toBe("forecast_sales");
    });

    it("should forecast specific products", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Predict Kerala Burger sales for next week",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/kerala burger/i);
      expect(response.body.message).toMatch(/₹.*confidence/);
    });

    it("should include inventory implications in forecasts", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "What will our inventory needs be based on sales forecasts?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/inventory|stock|need/i);
      expect(response.body.message).toMatch(/kg|pcs|buns|beef/i);
    });

    it("should handle different forecast periods", async () => {
      const testCases = [
        { message: "7 day forecast", period: "7" },
        { message: "forecast for next month", period: "30" },
        { message: "quarterly forecast", period: "90" }
      ];

      for (const testCase of testCases) {
        const response = await request(app)
          .post("/chat")
          .send({
            message: testCase.message,
            session_id: `${sessionId}_${testCase.period}`,
          })
          .expect(200);

        expect(response.body.message).toMatch(/forecast|predict/i);
        expect(response.body.metadata.intent).toBe("forecast_sales");
      }
    });
  });

  describe("Forecast Context and Follow-ups", () => {
    it("should maintain forecast context for follow-up questions", async () => {
      // Initial forecast
      await request(app)
        .post("/chat")
        .send({
          message: "Forecast Kerala Burger sales for next month",
          session_id: sessionId,
        })
        .expect(200);

      // Follow-up about inventory
      const response = await request(app)
        .post("/chat")
        .send({
          message: "What inventory do I need for that forecast?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/inventory|stock/i);
      expect(response.body.message).toMatch(/kerala burger|buns|beef/i);
    });

    it("should handle seasonal forecasting questions", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "How will seasonal trends affect next quarter's sales?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/seasonal|quarter|trend/i);
    });
  });

  describe("Forecast Accuracy and Confidence", () => {
    it("should provide confidence intervals", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Give me a confident sales prediction with ranges",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/confidence|%|range/i);
      expect(response.body.message).toMatch(/₹.*-.*₹/); // Revenue range format
    });

    it("should explain forecast methodology", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "How do you calculate sales forecasts?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/historical|trend|data|analysis/i);
    });
  });

  describe("Error Handling", () => {
    it("should handle forecasting for non-existent products", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Forecast sales for Pizza Deluxe", // Product not in our system
          session_id: sessionId,
        })
        .expect(200);

      // Should either clarify or suggest alternatives
      expect(response.body.message).toMatch(/not found|suggest|available|similar/i);
    });

    it("should handle invalid forecast periods", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Predict sales for next 365 days", // Very long period
          session_id: sessionId,
        })
        .expect(200);

      // Should provide reasonable alternatives
      expect(response.body.message).toMatch(/90 days|quarterly|shorter period/i);
    });
  });

  describe("Business Value", () => {
    it("should connect forecasts to business decisions", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Help me plan next month's operations with sales forecasts",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/staff|inventory|prepare|plan/i);
      expect(response.body.message).toMatch(/₹|revenue|sales/i);
    });

    it("should provide actionable recommendations", async () => {
      const response = await request(app)
        .post("/chat")
        .send({
          message: "Based on forecasts, what should I focus on?",
          session_id: sessionId,
        })
        .expect(200);

      expect(response.body.message).toMatch(/recommend|focus|priority|should/i);
    });
  });
});
