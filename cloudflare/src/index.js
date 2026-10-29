/**
 * BimaGyan AI — Cloudflare Workers AI Endpoint
 * Runs Llama 3.1 8B with the BimaGyan insurance LoRA adapter at the edge.
 *
 * Endpoints:
 *   POST /             — Generate response (FastAPI / Modal compatible)
 *   POST /api/generate — Standard JSON API
 *   GET /health        — Healthcheck
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── CORS preflight ─────────────────────────────────────────────────────────
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // ── Healthcheck ───────────────────────────────────────────────────────────
    if (url.pathname === "/health" || request.method === "GET") {
      return Response.json({
        status: "healthy",
        service: "BimaGyan Cloudflare Workers AI",
        model: env.BASE_MODEL || "@cf/meta/llama-3.1-8b-instruct-fp8",
        lora: env.LORA_NAME || "bimagyan-lora",
      }, {
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const body = await request.json();

      // Support both `inputs` (Modal/HF format) and `prompt` (standard format)
      const prompt = body.inputs || body.prompt || (body.data && body.data[0]) || "";
      const maxTokens = body.parameters?.max_new_tokens || body.max_tokens || 512;
      const temperature = body.parameters?.temperature || body.temperature || 0.2;

      if (!prompt.trim()) {
        return Response.json({ error: "Empty prompt" }, { status: 400 });
      }

      const modelId = env.BASE_MODEL || "@cf/meta/llama-3.1-8b-instruct-fp8";
      const loraId = env.LORA_NAME || "bimagyan-lora";

      const aiOptions = {
        prompt: prompt,
        max_tokens: Math.min(Number(maxTokens), 1024),
        temperature: Number(temperature),
      };

      // Attach LoRA adapter if configured
      if (loraId && loraId !== "none") {
        aiOptions.lora = loraId;
      }

      const result = await env.AI.run(modelId, aiOptions);
      const generatedText = result.response || result.result || "";

      // Return both generated_text (Modal format) and response (CF format) for full compatibility
      return Response.json({
        generated_text: generatedText.trim(),
        response: generatedText.trim(),
        model: modelId,
        lora: loraId,
      }, {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });

    } catch (err) {
      return Response.json({
        error: "Inference failed",
        detail: err.message,
      }, {
        status: 500,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }
  },
};
