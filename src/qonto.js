import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE_URL = 'https://thirdparty.qonto.com/v2';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');
const PDF_DIR = path.join(PROJECT_ROOT, 'pdf');

async function loadEnv() {
  const envPath = path.join(PROJECT_ROOT, '.env');
  try {
    const raw = await fs.readFile(envPath, 'utf8');
    for (const line of raw.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eq = trimmed.indexOf('=');
      if (eq === -1) continue;
      const key = trimmed.slice(0, eq).trim();
      const value = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, '');
      if (!(key in process.env)) process.env[key] = value;
    }
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
}

function getAuthHeader() {
  const slug = process.env.QONTO_ORGANIZATION_SLUG;
  const key = process.env.QONTO_SECRET_KEY;
  if (!slug || !key) {
    throw new Error('Missing credentials. Set QONTO_ORGANIZATION_SLUG and QONTO_SECRET_KEY in .env (see .env.example).');
  }
  return `${slug}:${key}`;
}

async function parseError(response) {
  let body;
  try {
    body = await response.json();
  } catch {
    body = await response.text().catch(() => '');
  }
  const status = response.status;
  if (status === 401) {
    return new Error('Qonto 401 Unauthorized — check QONTO_ORGANIZATION_SLUG / QONTO_SECRET_KEY and required API scopes.');
  }
  if (status === 422) {
    const details = typeof body === 'object' ? JSON.stringify(body.errors ?? body, null, 2) : body;
    return new Error(`Qonto 422 Validation error:\n${details}`);
  }
  if (status === 429) {
    return new Error('Qonto 429 Rate limit — try again later.');
  }
  const details = typeof body === 'object' ? JSON.stringify(body, null, 2) : body;
  return new Error(`Qonto ${status} ${response.statusText}\n${details}`);
}

export async function apiFetch(method, endpoint, { body, query, retry = true } = {}) {
  await loadEnv();
  const auth = getAuthHeader();
  const url = new URL(`${BASE_URL}${endpoint}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue;
      if (Array.isArray(v)) v.forEach((item) => url.searchParams.append(k, item));
      else url.searchParams.set(k, String(v));
    }
  }

  const headers = {
    Authorization: auth,
    Accept: 'application/json',
  };
  const init = { method, headers };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }

  const response = await fetch(url, init);

  if (response.status === 429 && retry) {
    await new Promise((r) => setTimeout(r, 2000));
    return apiFetch(method, endpoint, { body, query, retry: false });
  }
  if (response.status >= 500 && response.status < 600 && retry) {
    await new Promise((r) => setTimeout(r, 1000));
    return apiFetch(method, endpoint, { body, query, retry: false });
  }
  if (!response.ok) throw await parseError(response);

  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) return response.json();
  return response.text();
}

export async function downloadAttachmentPdf(attachmentId) {
  const { attachment } = await apiFetch('GET', `/attachments/${attachmentId}`);
  if (!attachment?.url) throw new Error(`Attachment ${attachmentId} has no download URL.`);
  return downloadFromUrl(attachment.url, attachment.file_name);
}

export async function downloadFromUrl(url, suggestedName) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Download failed: ${response.status} ${response.statusText}`);

  let filename = suggestedName;
  const disposition = response.headers.get('content-disposition');
  if (disposition) {
    const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i);
    if (match) filename = decodeURIComponent(match[1]);
  }
  if (!filename) filename = `document-${Date.now()}.pdf`;

  await fs.mkdir(PDF_DIR, { recursive: true });
  const finalPath = await resolveNoClobber(path.join(PDF_DIR, filename));
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.writeFile(finalPath, buffer);
  return finalPath;
}

async function resolveNoClobber(targetPath) {
  const ext = path.extname(targetPath);
  const base = targetPath.slice(0, targetPath.length - ext.length);
  let candidate = targetPath;
  let counter = 2;
  while (await exists(candidate)) {
    candidate = `${base}_(${counter})${ext}`;
    counter += 1;
  }
  return candidate;
}

async function exists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

export async function ping() {
  const data = await apiFetch('GET', '/organization');
  const org = data.organization ?? data;
  return {
    organization: org.name ?? org.slug ?? '(unknown)',
    slug: org.slug,
    bank_accounts: (org.bank_accounts ?? []).map((a) => ({
      id: a.id,
      iban: a.iban,
      balance: a.balance,
      currency: a.currency,
    })),
  };
}
