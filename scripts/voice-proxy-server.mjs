#!/usr/bin/env node
import http from 'node:http';
import handler from '../api/voice/infer.js';

const port = Number(process.env.PORT || process.env.VOICE_PROXY_PORT || 8790);
const host = process.env.HOST || process.env.VOICE_PROXY_HOST || '127.0.0.1';

function createResponseAdapter(res) {
  return {
    statusCode: 200,
    setHeader: (...args) => res.setHeader(...args),
    status(code) {
      this.statusCode = code;
      res.statusCode = code;
      return this;
    },
    json(payload) {
      if (!res.hasHeader('Content-Type')) {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
      }
      res.end(JSON.stringify(payload));
    },
    send(payload) {
      res.end(payload);
    },
    end(payload) {
      res.end(payload);
    },
  };
}

const server = http.createServer(async (req, res) => {
  const pathname = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`).pathname;

  if (pathname === '/health' || pathname === '/api/voice/health') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      ok: true,
      service: 'voice-proxy',
      configured: true,
      requiresApiKey: Boolean(process.env.VOICE_PROXY_API_KEY),
      upstream: process.env.VOICE_PROXY_UPSTREAM_URL || 'http://10.8.0.99:8000/infer',
    }));
    return;
  }

  if (pathname !== '/api/voice/infer' && pathname !== '/infer') {
    res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }

  try {
    await handler(req, createResponseAdapter(res));
  } catch (error) {
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
    }
    res.end(JSON.stringify({
      error: 'Voice proxy crashed',
      message: error instanceof Error ? error.message : String(error),
    }));
  }
});

server.listen(port, host, () => {
  console.log(`Voice proxy listening on http://${host}:${port}`);
  console.log('Voice endpoint: /api/voice/infer');
});