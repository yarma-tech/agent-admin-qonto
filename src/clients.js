import { apiFetch } from './qonto.js';

export async function listClients({ type, limit = 100 } = {}) {
  const query = { per_page: limit };
  if (type) query['filter[type]'] = type;
  const data = await apiFetch('GET', '/clients', { query });
  return data.clients ?? [];
}

export async function retrieveClient(id) {
  const data = await apiFetch('GET', `/clients/${id}`);
  return data.client ?? data;
}

export async function createClient(payload) {
  const data = await apiFetch('POST', '/clients', { body: payload });
  return data.client ?? data;
}

export async function updateClient(id, patch) {
  const data = await apiFetch('PATCH', `/clients/${id}`, { body: patch });
  return data.client ?? data;
}

function normalize(value) {
  if (!value) return '';
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\b(s\.?a\.?r\.?l\.?|s\.?a\.?s\.?|s\.?a\.?|eurl|sasu)\b/gi, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export async function findClients(query) {
  const needle = normalize(query);
  if (!needle) return [];
  const all = await listClients({ limit: 500 });
  const matches = all
    .map((c) => {
      const haystack = normalize([c.name, c.company_name, c.email].filter(Boolean).join(' '));
      if (!haystack) return null;
      if (haystack === needle) return { client: c, score: 3 };
      if (haystack.includes(needle)) return { client: c, score: 2 };
      const tokens = needle.split(' ');
      if (tokens.every((t) => haystack.includes(t))) return { client: c, score: 1 };
      return null;
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .map((m) => m.client);
  return matches;
}
