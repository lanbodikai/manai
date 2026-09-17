// Production static server, same-origin analysis proxy and read-only source browser.
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { datasetHandler } from './tools/dataset-handler.ts';

const root = path.resolve(process.env.DASHBOARD_DIST || '/app/dist');
const dataset = datasetHandler(process.env.DATASET_DB || '/cache/preview.sqlite');
const kinds = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript',
  '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };
const send = (res, status, body, kind = 'application/json') => {
  if (res.writableEnded || res.destroyed) return;
  res.writeHead(status, { 'Content-Type': kind, 'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
  res.end(body);
};
const fail = (res, status, code, message) => send(res, status, JSON.stringify({
  error: { code, message, retryable: status >= 500, request_id: randomUUID() },
}));

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname.startsWith('/api/datasets/')) {
      req.url = req.url.slice('/api/datasets'.length);
      return dataset.handle(req, res);
    }
    if (url.pathname === '/api/optimizations') {
      return fail(res, 501, 'OPTIMIZATION_UNAVAILABLE', 'Multi-fix modeling is not implemented. No action was taken.');
    }
    if (url.pathname.startsWith('/api/')) {
      if (!['GET', 'POST'].includes(req.method)) return fail(res, 405, 'INVALID_REQUEST', 'Method not available.');
      const reviewer = url.pathname.endsWith('/explanations');
      const target = reviewer ? process.env.REVIEWER_URL : (process.env.ANALYSIS_URL || 'http://analysis:8001');
      if (!target) return fail(res, 503, 'AGENT_UNAVAILABLE', 'Optional reviewer is not enabled.');
      const chunks = [];
      let size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > 65536) return fail(res, 413, 'INVALID_REQUEST', 'Request body exceeds the permitted size.');
        chunks.push(chunk);
      }
      const body = Buffer.concat(chunks);
      const upstreamUrl = new URL(target.replace(/\/$/, '') + req.url);
      const request = upstreamUrl.protocol === 'https:' ? httpsRequest : httpRequest;
      const upstream = request(upstreamUrl, { method: req.method, headers: {
        Accept: 'application/json', 'Content-Type': 'application/json', 'Content-Length': body.length,
      } }, response => {
        const data = [];
        response.on('data', chunk => data.push(chunk));
        response.on('end', () => {
          clearTimeout(timer);
          send(res, response.statusCode, Buffer.concat(data), response.headers['content-type'] || 'application/json');
        });
        response.on('error', () => upstream.destroy(new Error('Upstream response failed')));
      });
      const timer = setTimeout(() => upstream.destroy(new Error('Upstream deadline')), reviewer ? 31000 : 20000);
      upstream.on('error', () => {
        clearTimeout(timer);
        fail(res, 503, reviewer ? 'AGENT_UNAVAILABLE' : 'UPSTREAM_UNAVAILABLE',
          reviewer ? 'Optional reviewer unavailable.' : 'Analysis service unavailable.');
      });
      res.on('close', () => { clearTimeout(timer); upstream.destroy(); });
      upstream.end(body);
      return;
    }
    if (req.method !== 'GET') return fail(res, 405, 'INVALID_REQUEST', 'Method not available.');
    const file = path.resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
    if (!file.startsWith(root + path.sep)) return fail(res, 404, 'ROUTE_NOT_AVAILABLE', 'Route not found.');
    try { send(res, 200, await readFile(file), kinds[path.extname(file)] || 'application/octet-stream'); }
    catch { fail(res, 404, 'ROUTE_NOT_AVAILABLE', 'Route not found.'); }
  } catch {
    fail(res, 400, 'INVALID_REQUEST', 'Request could not be read.');
  }
});
server.on('close', dataset.close);
server.listen(Number(process.env.PORT || 3000), process.env.HOST || '0.0.0.0');
