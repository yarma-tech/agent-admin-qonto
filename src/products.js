import { apiFetch } from './qonto.js';

export async function listProducts({ limit = 100 } = {}) {
  const data = await apiFetch('GET', '/products', { query: { per_page: limit } });
  return data.products ?? [];
}

export async function retrieveProduct(id) {
  const data = await apiFetch('GET', `/products/${id}`);
  return data.product ?? data;
}

export async function createProduct(payload) {
  const data = await apiFetch('POST', '/products', { body: { product: payload } });
  return data.product ?? data;
}

export async function deleteProduct(id) {
  await apiFetch('DELETE', `/products/${id}`);
  return { id, deleted: true };
}

export async function replaceProduct(id, newPayload) {
  const deleted = await deleteProduct(id);
  const created = await createProduct(newPayload);
  return { deleted_id: deleted.id, new: created };
}

function normalize(value) {
  if (!value) return '';
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export async function findProducts(query) {
  const needle = normalize(query);
  if (!needle) return [];
  const all = await listProducts({ limit: 500 });
  const matches = all
    .map((p) => {
      const haystack = normalize([p.title, p.description].filter(Boolean).join(' '));
      if (!haystack) return null;
      if (haystack === needle) return { product: p, score: 3 };
      if (haystack.includes(needle)) return { product: p, score: 2 };
      const tokens = needle.split(' ');
      if (tokens.every((t) => haystack.includes(t))) return { product: p, score: 1 };
      return null;
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .map((m) => m.product);
  return matches;
}
