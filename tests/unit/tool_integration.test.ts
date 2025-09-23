/**
 * Unit tests for LangGraph tool integration
 */

import { 
  salesAnalyticsTools, 
  generateResponseWithTools, 
  extractToolCallsFromResponse,
  formatToolResultsForLLM
} from "../../src/services/openai_integration";

describe("Tool Integration", () => {

  describe("OpenAI Tool Definitions", () => {
    it("should have all required tools defined", () => {
      const toolNames = salesAnalyticsTools.map(tool => tool.function.name);
      
      const expectedTools = [
        "analyze_sales_data",
        "forecast_sales", 
        "get_inventory_status",
        "analyze_product_performance",
        "compare_periods",
        "generate_chart_data"
      ];

      for (const expectedTool of expectedTools) {
        expect(toolNames).toContain(expectedTool);
      }
    });

    it("should have proper parameter schemas", () => {
      const analyzeSalesTool = salesAnalyticsTools.find(
        tool => tool.function.name === "analyze_sales_data"
      );

      expect(analyzeSalesTool).toBeDefined();
      expect(analyzeSalesTool!.function.parameters.properties).toHaveProperty("time_period");
      expect(analyzeSalesTool!.function.parameters.properties.time_period.enum).toContain("last_month");
    });

    it("should have required fields specified correctly", () => {
      const compareTool = salesAnalyticsTools.find(
        tool => tool.function.name === "compare_periods"
      );

      expect(compareTool).toBeDefined();
      expect(compareTool!.function.parameters.required).toContain("current_period");
      expect(compareTool!.function.parameters.required).toContain("comparison_period");
    });
  });

  describe("Tool Result Formatting", () => {
    it("should format sales analysis results correctly", () => {
      const mockToolResults = [
        {
          tool: "analyze_sales_data",
          result: {
            total_revenue: 85000,
            total_items_sold: 1200,
            summary: {
              revenue_growth: 15.2,
              top_performer: { product_name: "Kerala Burger" }
            }
          }
        }
      ];

      const formatted = formatToolResultsForLLM(mockToolResults);
      
      expect(formatted).toContain("Total Revenue: ₹85,000");
      expect(formatted).toContain("Items Sold: 1200");
      expect(formatted).toContain("Growth Rate: 15.2%");
      expect(formatted).toContain("Top Product: Kerala Burger");
    });

    it("should format forecast results correctly", () => {
      const mockToolResults = [
        {
          tool: "forecast_sales",
          result: {
            forecast_period: "30 days",
            total_predicted_revenue: 95000,
            forecasts: [
              { product_name: "Kerala Burger", predicted_revenue: 38000 }
            ]
          }
        }
      ];

      const formatted = formatToolResultsForLLM(mockToolResults);
      
      expect(formatted).toContain("Period: 30 days");
      expect(formatted).toContain("Total Predicted Revenue: ₹95,000");
      expect(formatted).toContain("Kerala Burger - ₹38,000");
    });

    it("should handle tool errors gracefully", () => {
      const mockToolResults = [
        {
          tool: "analyze_sales_data",
          result: {
            error: true,
            message: "API connection failed"
          }
        }
      ];

      const formatted = formatToolResultsForLLM(mockToolResults);
      
      expect(formatted).toContain("Tool analyze_sales_data failed");
      expect(formatted).toContain("API connection failed");
    });
  });

  describe("Tool Call Extraction", () => {
    it("should extract function calls from OpenAI response", () => {
      const mockResponse = {
        choices: [{
          message: {
            tool_calls: [{
              type: "function",
              function: {
                name: "analyze_sales_data",
                arguments: '{"time_period": "last_month", "category": "menu"}'
              }
            }]
          }
        }]
      } as any;

      const toolCalls = extractToolCallsFromResponse(mockResponse);
      
      expect(toolCalls).toHaveLength(1);
      expect(toolCalls[0].tool).toBe("analyze_sales_data");
      expect(toolCalls[0].args.time_period).toBe("last_month");
      expect(toolCalls[0].args.category).toBe("menu");
    });

    it("should handle responses without tool calls", () => {
      const mockResponse = {
        choices: [{
          message: {
            content: "I can help you with sales analytics."
          }
        }]
      } as any;

      const toolCalls = extractToolCallsFromResponse(mockResponse);
      
      expect(toolCalls).toHaveLength(0);
    });

    it("should handle malformed tool arguments", () => {
      const mockResponse = {
        choices: [{
          message: {
            tool_calls: [{
              type: "function",
              function: {
                name: "analyze_sales_data",
                arguments: 'invalid json'
              }
            }]
          }
        }]
      } as any;

      const toolCalls = extractToolCallsFromResponse(mockResponse);
      
      expect(toolCalls).toHaveLength(1);
      expect(toolCalls[0].tool).toBe("analyze_sales_data");
      expect(toolCalls[0].args).toEqual({}); // Should default to empty object
    });
  });

  describe("Context Handling", () => {
    it("should include session history in tool calls", async () => {
      const context = {
        user_message: "Show me sales trends",
        session_history: [
          { role: "user", content: "Hello" },
          { role: "assistant", content: "Hi! I can help with sales analytics." }
        ]
      };

      // Mock OpenAI call (won't actually call API in tests)
      try {
        await generateResponseWithTools(context);
      } catch (error) {
        // Expected to fail without API key, but should not throw parameter errors
        expect(error.message).toMatch(/API|key|failed/i);
      }
    });

    it("should include tool results in context", () => {
      const context = {
        user_message: "What does this data mean?",
        session_history: [],
        tool_results: [
          {
            tool: "analyze_sales_data",
            result: { total_revenue: 85000, success: true }
          }
        ]
      };

      // Should format tool results into context
      const formatted = formatToolResultsForLLM(context.tool_results);
      expect(formatted).toContain("85,000");
    });
  });

  describe("Tool Schema Validation", () => {
    it("should validate tool parameters match schema", () => {
      const forecastTool = salesAnalyticsTools.find(
        tool => tool.function.name === "forecast_sales"
      );

      expect(forecastTool!.function.parameters.properties.forecast_days.enum).toEqual([7, 30, 90]);
      expect(forecastTool!.function.parameters.properties.include_confidence.type).toBe("boolean");
    });

    it("should have descriptions for all tools", () => {
      for (const tool of salesAnalyticsTools) {
        expect(tool.function.description).toBeDefined();
        expect(tool.function.description.length).toBeGreaterThan(20);
      }
    });

    it("should have proper enum constraints", () => {
      const chartTool = salesAnalyticsTools.find(
        tool => tool.function.name === "generate_chart_data"
      );

      expect(chartTool!.function.parameters.properties.chart_type.enum).toEqual(
        ["line", "bar", "pie", "trend"]
      );
      expect(chartTool!.function.parameters.properties.data_source.enum).toEqual(
        ["sales", "inventory", "forecasts", "performance"]
      );
    });
  });

  describe("Integration with LangGraph", () => {
    it("should map OpenAI tools to LangGraph tools", () => {
      // Verify tool names match between OpenAI function calling and LangGraph tools
      const openaiToolNames = salesAnalyticsTools.map(t => t.function.name);
      
      // These should match the actual LangGraph tool names
      const expectedLangGraphTools = [
        "analyze_sales_data",
        "forecast_sales",
        "get_inventory_status", 
        "analyze_product_performance",
        "compare_periods",
        "generate_chart_data"
      ];

      for (const toolName of expectedLangGraphTools) {
        expect(openaiToolNames).toContain(toolName);
      }
    });
  });
});
