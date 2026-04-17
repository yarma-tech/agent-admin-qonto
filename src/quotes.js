import { apiFetch, downloadAttachmentPdf, downloadFromUrl } from './qonto.js';

export async function listQuotes({ clientId, from, to, limit = 100 } = {}) {
  const query = { per_page: limit };
  if (clientId) query['filter[client_id]'] = clientId;
  if (from) query['filter[issue_date_from]'] = from;
  if (to) query['filter[issue_date_to]'] = to;
  const data = await apiFetch('GET', '/quotes', { query });
  return data.quotes ?? [];
}

export async function retrieveQuote(id) {
  const data = await apiFetch('GET', `/quotes/${id}`);
  return data.quote ?? data;
}

function normalize(value) {
  if (!value) return '';
  return String(value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export async function findQuotes(term) {
  const needle = normalize(term);
  if (!needle) return [];
  const quotes = await listQuotes({ limit: 500 });
  return quotes.filter((q) => {
    const haystack = normalize(
      [q.number, q.header, q.footer, q.client?.name, q.purchase_order, (q.items ?? []).map((i) => i.title).join(' ')]
        .filter(Boolean)
        .join(' ')
    );
    return haystack.includes(needle);
  });
}

export async function createQuote(payload) {
  validateDiscounts(payload);
  const data = await apiFetch('POST', '/quotes', { body: { quote: payload } });
  const quote = data.quote ?? data;
  const pdfPath = await downloadQuotePdf(quote);
  return { ...quote, pdf_path: pdfPath };
}

export async function updateQuote(id, patch) {
  const current = await retrieveQuote(id);
  if (current.status && current.status !== 'draft') {
    throw new Error(`Quote ${current.number ?? id} is ${current.status}, only drafts can be modified.`);
  }
  validateDiscounts({ ...current, ...patch });
  const data = await apiFetch('PATCH', `/quotes/${id}`, { body: { quote: patch } });
  return data.quote ?? data;
}

export async function sendQuote(id, { sendTo, emailTitle, emailBody, copyToSelf = true }) {
  if (!Array.isArray(sendTo) || sendTo.length === 0) {
    throw new Error('sendTo must be a non-empty array of email addresses.');
  }
  if (!emailTitle) throw new Error('emailTitle is required.');
  const body = { send_to: sendTo, email_title: emailTitle, copy_to_self: copyToSelf };
  if (emailBody) body.email_body = emailBody;
  const data = await apiFetch('POST', `/quotes/${id}/send`, { body });
  return data;
}

export async function downloadQuotePdf(quote) {
  if (quote.attachment_id) return downloadAttachmentPdf(quote.attachment_id);
  if (quote.pdf_url) return downloadFromUrl(quote.pdf_url, `${quote.number ?? quote.id}.pdf`);
  if (quote.quote_url) return downloadFromUrl(quote.quote_url, `${quote.number ?? quote.id}.pdf`);
  throw new Error('No attachment_id / pdf_url / quote_url available for this quote.');
}

function validateDiscounts(payload) {
  if (payload.discount) assertDiscount(payload.discount, 'quote');
  for (const item of payload.items ?? []) {
    if (item.discount) assertDiscount(item.discount, `item "${item.title ?? '?'}"`);
  }
}

function assertDiscount(discount, label) {
  const { type, value } = discount;
  if (type !== 'percentage' && type !== 'amount') {
    throw new Error(`Invalid discount on ${label}: type must be "percentage" or "amount".`);
  }
  const num = Number(value);
  if (!Number.isFinite(num) || num < 0) {
    throw new Error(`Invalid discount on ${label}: value must be a non-negative number.`);
  }
  if (type === 'percentage' && num > 100) {
    throw new Error(`Invalid discount on ${label}: percentage > 100%.`);
  }
}
