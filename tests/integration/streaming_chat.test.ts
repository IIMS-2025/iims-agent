/**
 * Integration tests for streaming chat functionality
 */

import request from "supertest";
import app from "../../src/index";

describe("Streaming Chat Integration", () => {
  let sessionId: string;

  beforeEach(() => {
    sessionId = `stream_test_${Date.now()}`;
  });

  describe("Server-Sent Events Streaming", () => {
    it("should stream responses with typing simulation", (done) => {
      const req = request(app)
        .post("/chat")
        .send({
          message: "Show me comprehensive sales analysis",
          session_id: sessionId,
          stream: true,
        });

      let chunks: string[] = [];
      let isDone = false;

      req.expect(200)
        .expect("Content-Type", /text\/event-stream/)
        .expect("Cache-Control", "no-cache")
        .expect("Connection", "keep-alive")
        .end((err) => {
          if (err) return done(err);
        });

      req.on("data", (chunk) => {
        const chunkStr = chunk.toString();
        
        // Parse SSE data
        const lines = chunkStr.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.substring(6));
              
              if (data.chunk) {
                chunks.push(data.chunk);
                expect(data.progress).toBeGreaterThanOrEqual(0);
                expect(data.progress).toBeLessThanOrEqual(1);
              }
              
              if (data.done) {
                isDone = true;
                expect(data.session_id).toBe(sessionId);
                expect(data.metadata).toBeDefined();
                
                // Verify streaming assembled correctly
                const fullMessage = chunks[chunks.length - 1] || "";
                expect(fullMessage.length).toBeGreaterThan(50); // Reasonable response length
                expect(fullMessage).toMatch(/📈|📊|🔮|💡/); // Should contain emojis
                
                done();
              }
            } catch (parseError) {
              // Ignore malformed chunks
            }
          }
        }
      });

      req.on("error", done);
      
      // Timeout after 10 seconds
      setTimeout(() => {
        if (!isDone) {
          done(new Error("Streaming response timeout"));
        }
      }, 10000);
    });

    it("should handle streaming errors gracefully", (done) => {
      const req = request(app)
        .post("/chat")
        .send({
          message: "", // Invalid empty message
          session_id: sessionId,
          stream: true,
        });

      req.expect(400).end(done);
    });
  });

  describe("Streaming Performance", () => {
    it("should stream responses within reasonable time", (done) => {
      const startTime = Date.now();
      let firstChunkTime: number;
      let completionTime: number;

      const req = request(app)
        .post("/chat")
        .send({
          message: "Analyze sales trends and forecast next month",
          session_id: sessionId,
          stream: true,
        })
        .expect(200);

      let chunkCount = 0;

      req.on("data", (chunk) => {
        const chunkStr = chunk.toString();
        
        if (chunkStr.includes('"chunk"') && !firstChunkTime) {
          firstChunkTime = Date.now();
          expect(firstChunkTime - startTime).toBeLessThan(2000); // First chunk within 2s
        }
        
        if (chunkStr.includes('"done":true')) {
          completionTime = Date.now();
          
          // Performance assertions
          expect(completionTime - startTime).toBeLessThan(10000); // Complete within 10s
          expect(chunkCount).toBeGreaterThan(5); // Should have multiple chunks
          
          done();
        }
        
        chunkCount++;
      });

      req.on("error", done);
    });
  });

  describe("Streaming with Analytics Context", () => {
    it("should maintain session context during streaming", async () => {
      // Set up context with initial message
      await request(app)
        .post("/chat")
        .send({
          message: "Show me Kerala Burger performance",
          session_id: sessionId,
        })
        .expect(200);

      // Test streaming follow-up
      return new Promise<void>((resolve, reject) => {
        const req = request(app)
          .post("/chat")
          .send({
            message: "Now stream the forecast for that product",
            session_id: sessionId,
            stream: true,
          })
          .expect(200);

        let fullResponse = "";

        req.on("data", (chunk) => {
          const chunkStr = chunk.toString();
          
          if (chunkStr.includes('"chunk"')) {
            try {
              const data = JSON.parse(chunkStr.substring(6));
              if (data.chunk) {
                fullResponse = data.chunk;
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
          
          if (chunkStr.includes('"done":true')) {
            // Verify context was used
            expect(fullResponse.toLowerCase()).toMatch(/kerala burger|forecast/i);
            resolve();
          }
        });

        req.on("error", reject);
      });
    });
  });

  describe("Concurrent Streaming Sessions", () => {
    it("should handle multiple concurrent streaming sessions", async () => {
      const sessions = [
        `concurrent_1_${Date.now()}`,
        `concurrent_2_${Date.now()}`,
        `concurrent_3_${Date.now()}`
      ];

      const promises = sessions.map((sessionId, index) => {
        return new Promise<void>((resolve, reject) => {
          const req = request(app)
            .post("/chat")
            .send({
              message: `Analyze sales trends for session ${index + 1}`,
              session_id: sessionId,
              stream: true,
            })
            .expect(200);

          let completed = false;

          req.on("data", (chunk) => {
            if (chunk.toString().includes('"done":true') && !completed) {
              completed = true;
              resolve();
            }
          });

          req.on("error", reject);
          
          setTimeout(() => {
            if (!completed) {
              reject(new Error(`Session ${sessionId} timeout`));
            }
          }, 8000);
        });
      });

      // All streams should complete successfully
      await Promise.all(promises);
    });
  });

  describe("Streaming Error Recovery", () => {
    it("should recover from streaming interruptions", (done) => {
      const req = request(app)
        .post("/chat")
        .send({
          message: "Very long analysis request that might fail during streaming",
          session_id: sessionId,
          stream: true,
        })
        .expect(200);

      let errorReceived = false;

      req.on("data", (chunk) => {
        const chunkStr = chunk.toString();
        
        if (chunkStr.includes('"error":true')) {
          errorReceived = true;
          expect(chunkStr).toMatch(/error|failed/i);
        }
        
        if (chunkStr.includes('"done":true')) {
          // Should complete even if there was an error
          done();
        }
      });

      req.on("error", (err) => {
        // Network errors should be handled gracefully
        expect(err).toBeDefined();
        done();
      });
    });
  });
});
