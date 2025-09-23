/**
 * OpenAI Function Calling Integration
 * Implements the exact OpenAI tool definitions specified in the README
 */

import { OpenAI } from "openai";

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Tool definitions for OpenAI function calling (from README specification)
export const salesAnalyticsTools: OpenAI.Chat.Completions.ChatCompletionTool[] =
  [
    {
      type: "function",
      function: {
        name: "analyze_sales_data",
        description:
          "Analyze sales trends and patterns for specific time periods and products",
        parameters: {
          type: "object",
          properties: {
            time_period: {
              type: "string",
              enum: ["last_week", "last_month", "last_quarter"],
              description: "Predefined time period for analysis",
            },
            product_id: {
              type: "string",
              description: "Specific product UUID to analyze",
            },
            category: {
              type: "string",
              description: "Product category filter",
            },
            group_by: {
              type: "string",
              enum: ["day", "week", "month"],
              description: "Aggregation level for the analysis",
            },
          },
        },
      },
    },
    {
      type: "function",
      function: {
        name: "forecast_sales",
        description: "Generate sales forecasts based on historical data",
        parameters: {
          type: "object",
          properties: {
            product_id: {
              type: "string",
              description: "Specific product UUID to forecast",
            },
            forecast_days: {
              type: "number",
              enum: [7, 30, 90],
              description: "Number of days to forecast",
            },
            include_confidence: {
              type: "boolean",
              description: "Whether to include confidence intervals",
            },
          },
        },
      },
    },
    {
      type: "function",
      function: {
        name: "get_inventory_status",
        description: "Get current inventory levels and stock status",
        parameters: {
          type: "object",
          properties: {
            filter_status: {
              type: "string",
              enum: ["low_stock", "out_of_stock", "expiring_soon"],
              description: "Filter by specific stock status",
            },
            product_id: {
              type: "string",
              description: "Specific product UUID",
            },
            include_sales_context: {
              type: "boolean",
              description: "Include sales velocity and recommendations",
            },
          },
        },
      },
    },
    {
      type: "function",
      function: {
        name: "analyze_product_performance",
        description: "Analyze product performance metrics and rankings",
        parameters: {
          type: "object",
          properties: {
            time_period: {
              type: "string",
              enum: ["last_week", "last_month", "last_quarter"],
              description: "Analysis period",
            },
            metric: {
              type: "string",
              enum: ["revenue", "quantity_sold", "profit_margin"],
              description: "Performance metric to analyze",
            },
            top_n: {
              type: "number",
              description: "Number of top performers to return",
            },
            category: {
              type: "string",
              description: "Filter by product category",
            },
          },
        },
      },
    },
    {
      type: "function",
      function: {
        name: "compare_periods",
        description: "Compare metrics between different time periods",
        parameters: {
          type: "object",
          properties: {
            current_period: {
              type: "string",
              description: "Current analysis period",
            },
            comparison_period: {
              type: "string",
              description: "Period to compare against",
            },
            metric: {
              type: "string",
              enum: ["revenue", "sales_volume", "profit_margin"],
              description: "Metric to compare",
            },
            product_id: {
              type: "string",
              description: "Specific product for comparison",
            },
          },
          required: ["current_period", "comparison_period"],
        },
      },
    },
    {
      type: "function",
      function: {
        name: "generate_chart_data",
        description: "Generate data formatted for chart visualization",
        parameters: {
          type: "object",
          properties: {
            chart_type: {
              type: "string",
              enum: ["line", "bar", "pie", "trend"],
              description: "Type of chart to generate",
            },
            data_source: {
              type: "string",
              enum: ["sales", "inventory", "forecasts", "performance"],
              description: "Data source for the chart",
            },
            time_period: {
              type: "string",
              description: "Time range for chart data",
            },
            product_filter: {
              type: "string",
              description: "Filter by product or category",
            },
          },
          required: ["chart_type", "data_source"],
        },
      },
    },
  ];

export async function generateResponseWithTools(context: {
  user_message: string;
  session_history: Array<{ role: string; content: string }>;
  extracted_slots?: Record<string, any>;
  tool_results?: Array<{ tool: string; result: any }>;
}): Promise<OpenAI.Chat.Completions.ChatCompletion> {
  const systemPrompt = `You are a sales analytics and forecasting assistant for Kochi Burger Junction. You help analyze sales trends, predict future performance, and provide data-driven insights. Use the provided tools to query sales data, inventory levels, and generate forecasts. Be conversational like ChatGPT but focus on actionable business insights. Present data clearly with key metrics, trends, and recommendations. If you need specific data, use the available tools. Keep responses engaging but under 400 words. Use emojis sparingly for key insights (📈 📉 💡 ⚠️).`;

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: systemPrompt },
    ...context.session_history.map((msg) => ({
      role: msg.role as "user" | "assistant",
      content: msg.content,
    })),
    { role: "user", content: context.user_message },
  ];

  // Add tool results context if available
  if (context.tool_results && context.tool_results.length > 0) {
    const toolContext = `\n\nTool Results: ${JSON.stringify(
      context.tool_results,
      null,
      2
    )}`;
    messages[messages.length - 1].content += toolContext;
  }

  try {
    const response = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      messages,
      tools: salesAnalyticsTools,
      tool_choice: "auto",
      max_tokens: 800,
      temperature: 0.7,
      stream: false,
    });

    return response;
  } catch (error: any) {
    // Return error response in expected format
    throw new Error(`OpenAI API call failed: ${error.message}`);
  }
}

export async function generateStreamingResponseWithTools(
  context: {
    user_message: string;
    session_history: Array<{ role: string; content: string }>;
    extracted_slots?: Record<string, any>;
    tool_results?: Array<{ tool: string; result: any }>;
  },
  onChunk?: (chunk: string) => void
): Promise<string> {
  const systemPrompt = `You are a sales analytics and forecasting assistant for Kochi Burger Junction. You help analyze sales trends, predict future performance, and provide data-driven insights. Use the provided tools to query sales data, inventory levels, and generate forecasts. Be conversational like ChatGPT but focus on actionable business insights. Present data clearly with key metrics, trends, and recommendations. If you need specific data, use the available tools. Keep responses engaging but under 400 words. Use emojis sparingly for key insights (📈 📉 💡 ⚠️).`;

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: systemPrompt },
    ...context.session_history.map((msg) => ({
      role: msg.role as "user" | "assistant",
      content: msg.content,
    })),
    { role: "user", content: context.user_message },
  ];

  // Add tool results context if available
  if (context.tool_results && context.tool_results.length > 0) {
    const toolContext = `\n\nTool Results: ${JSON.stringify(
      context.tool_results,
      null,
      2
    )}`;
    messages[messages.length - 1].content += toolContext;
  }

  try {
    const stream = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      messages,
      tools: salesAnalyticsTools,
      tool_choice: "auto",
      max_tokens: 800,
      temperature: 0.7,
      stream: true,
    });

    let fullResponse = "";

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || "";
      if (content) {
        fullResponse += content;
        if (onChunk) {
          onChunk(content);
        }
      }
    }

    return fullResponse;
  } catch (error: any) {
    throw new Error(`OpenAI streaming API call failed: ${error.message}`);
  }
}

export function extractToolCallsFromResponse(
  response: OpenAI.Chat.Completions.ChatCompletion
): Array<{ tool: string; args: any }> {
  const toolCalls: Array<{ tool: string; args: any }> = [];

  const choice = response.choices[0];
  if (choice?.message?.tool_calls) {
    for (const toolCall of choice.message.tool_calls) {
      if (toolCall.type === "function") {
        toolCalls.push({
          tool: toolCall.function.name,
          args: JSON.parse(toolCall.function.arguments || "{}"),
        });
      }
    }
  }

  return toolCalls;
}

export function formatToolResultsForLLM(
  toolResults: Array<{ tool: string; result: any }>
): string {
  return toolResults
    .map((tr) => {
      const result = tr.result;

      if (result.error) {
        return `Tool ${tr.tool} failed: ${result.message}`;
      }

      // Format successful results by tool type
      switch (tr.tool) {
        case "analyze_sales_data":
          return `Sales Analysis Results:
        - Total Revenue: ₹${result.total_revenue?.toLocaleString() || "N/A"}
        - Items Sold: ${result.total_items_sold || "N/A"}
        - Growth Rate: ${result.summary?.revenue_growth || "N/A"}%
        - Top Product: ${result.summary?.top_performer?.product_name || "N/A"}`;

        case "forecast_sales":
          const forecasts = result.forecasts || [];
          return `Sales Forecast Results:
        - Period: ${result.forecast_period || "N/A"}
        - Total Predicted Revenue: ₹${
          result.total_predicted_revenue?.toLocaleString() || "N/A"
        }
        - Products: ${forecasts.length} forecasted
        - Key Forecast: ${forecasts[0]?.product_name || "N/A"} - ₹${
            forecasts[0]?.predicted_revenue?.toLocaleString() || "N/A"
          }`;

        case "get_inventory_status":
          return `Inventory Status Results:
        - Total Items: ${result.total_items || "N/A"}
        - Low Stock: ${result.summary?.total_low_stock || "N/A"}
        - Out of Stock: ${result.summary?.total_out_of_stock || "N/A"}
        - Expiring Soon: ${result.summary?.total_expiring_soon || "N/A"}`;

        default:
          return `${tr.tool} completed successfully with ${
            Object.keys(result).length
          } data points`;
      }
    })
    .join("\n\n");
}

// Export types for use in server
export interface ToolCallContext {
  user_message: string;
  session_history: Array<{ role: string; content: string }>;
  extracted_slots?: Record<string, any>;
  tool_results?: Array<{ tool: string; result: any }>;
}
