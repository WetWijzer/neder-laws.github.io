const DEFAULT_ALLOWED_ORIGINS = [
  'https://portland-laws.github.io',
  'https://211-ai.github.io',
  'http://localhost:5173',
  'http://127.0.0.1:5173',
];

function parseAllowedOrigins() {
  return (process.env.VOICE_PROXY_ALLOWED_ORIGINS || process.env.OPENROUTER_PROXY_ALLOWED_ORIGINS || DEFAULT_ALLOWED_ORIGINS.join(','))
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function setCorsHeaders(req, res) {
  const origin = req.headers.origin || '';
  const allowedOrigins = parseAllowedOrigins();
  const allowedOrigin = allowedOrigins.includes(origin) ? origin : allowedOrigins[0];
  const requestedHeaders = req.headers['access-control-request-headers'];
  const allowHeaders = requestedHeaders || 'Content-Type';

  res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', allowHeaders);
  res.setHeader('Access-Control-Max-Age', '86400');
}

function readRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;

    req.on('data', (chunk) => {
      total += chunk.length;
      if (total > 50 * 1024 * 1024) {
        reject(new Error('Audio upload too large'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

export default async function handler(req, res) {
  setCorsHeaders(req, res);

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const upstreamUrl = process.env.VOICE_PROXY_UPSTREAM_URL || 'http://10.8.0.99:8000/infer';
  const apiKey = process.env.VOICE_PROXY_API_KEY;

  try {
    const body = await readRawBody(req);
    const contentType = req.headers['content-type'];

    if (!contentType) {
      res.status(400).json({ error: 'Content-Type is required' });
      return;
    }

    const upstreamHeaders = {
      'content-type': contentType,
    };
    if (apiKey) {
      upstreamHeaders['x-api-key'] = apiKey;
    }

    const upstream = await fetch(upstreamUrl, {
      method: 'POST',
      headers: upstreamHeaders,
      body,
    });

    res.status(upstream.status);
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/octet-stream');
    const disposition = upstream.headers.get('content-disposition');
    if (disposition) {
      res.setHeader('Content-Disposition', disposition);
    }
    res.send(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    res.status(500).json({
      error: 'Voice proxy failed',
      message: error instanceof Error ? error.message : String(error),
    });
  }
}