import { LLM_CONFIG } from './llmConfig';

type ChatRole = 'system' | 'user' | 'assistant';

export interface OpenRouterMessage {
  role: ChatRole;
  content: string;
}

export interface OpenRouterGenerateOptions {
  model?: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  topK?: number;
  repetitionPenalty?: number;
  signal?: AbortSignal;
}

export class OpenRouterLLMService {
  isConfigured(): boolean {
    const baseUrl = LLM_CONFIG.OPENROUTER_BASE_URL;
    const directOpenRouter = baseUrl.includes('openrouter.ai');
    return Boolean(
      LLM_CONFIG.OPENROUTER_ENABLED &&
      baseUrl &&
      (LLM_CONFIG.OPENROUTER_API_KEY || !directOpenRouter),
    );
  }

  getDefaultModel(preferThinking = false): string {
    return preferThinking
      ? LLM_CONFIG.OPENROUTER_THINKING_MODEL
      : LLM_CONFIG.OPENROUTER_DEFAULT_MODEL;
  }

  async generateText(
    prompt: string,
    options: OpenRouterGenerateOptions = {},
  ): Promise<string> {
    return this.generateChat(
      [
        { role: 'system', content: 'You are a concise, helpful assistant.' },
        { role: 'user', content: prompt },
      ],
      options,
    );
  }

  async generateChat(
    messages: OpenRouterMessage[],
    options: OpenRouterGenerateOptions = {},
  ): Promise<string> {
    if (!this.isConfigured()) {
      throw new Error('OpenRouter fallback is not configured. Set VITE_OPENROUTER_API_KEY for direct OpenRouter calls, or route through a non-OpenRouter VITE_OPENROUTER_BASE_URL proxy.');
    }

    const response = await fetch(`${LLM_CONFIG.OPENROUTER_BASE_URL.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(LLM_CONFIG.OPENROUTER_API_KEY ? { Authorization: `Bearer ${LLM_CONFIG.OPENROUTER_API_KEY}` } : {}),
        ...(LLM_CONFIG.OPENROUTER_SITE_URL ? { 'HTTP-Referer': LLM_CONFIG.OPENROUTER_SITE_URL } : {}),
        ...(LLM_CONFIG.OPENROUTER_SITE_NAME ? { 'X-OpenRouter-Title': LLM_CONFIG.OPENROUTER_SITE_NAME } : {}),
      },
      body: JSON.stringify({
        model: options.model || this.getDefaultModel(),
        messages,
        max_tokens: options.maxTokens ?? 100,
        temperature: options.temperature ?? 0.1,
        top_p: options.topP,
        top_k: options.topK ?? 50,
        repetition_penalty: options.repetitionPenalty ?? 1.05,
      }),
      signal: options.signal,
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`OpenRouter request failed (${response.status}): ${body.slice(0, 300)}`);
    }

    const payload = await response.json();
    const text = payload?.choices?.[0]?.message?.content;
    if (typeof text !== 'string' || !text.trim()) {
      throw new Error('OpenRouter returned an empty response.');
    }

    return this.cleanText(text);
  }

  private cleanText(text: string): string {
    return text
      .replace(/<\|[^>]+?\|>/g, '')
      .trim();
  }
}

export const openRouterLLMService = new OpenRouterLLMService();
