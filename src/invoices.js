import { apiFetch, downloadAttachmentPdf, downloadFromUrl } from './qonto.js';

export async function listInvoices({ status, clientId, from, to, limit = 100 } = {}) {
  const query = { per_page: limit };
  if (status) query['filter[status]'] = status;
  if (clientId) query['filter[client_id]'] = clientId;
  if (from) query['filter[issue_date_from]'] = from;
  if (to) query['filter[issue_date_to]'] = to;
  const data = await apiFetch('GET', '/client_invoices', { query });
  return data.client_invoices ?? [];
}

export async function retrieveInvoice(id) {
  const data = await apiFetch('GET', `/client_invoices/${id}`);
  return data.client_invoice ?? data;
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

export async function findInvoices(term) {
  const needle = normalize(term);
  if (!needle) return [];
  const invoices = await listInvoices({ limit: 500 });
  return invoices.filter((inv) => {
    const haystack = normalize(
      [inv.number, inv.header, inv.footer, inv.client?.name, inv.purchase_order, (inv.items ?? []).map((i) => i.title).join(' ')]
        .filter(Boolean)
        .join(' ')
    );
    return haystack.includes(needle);
  });
}

export async function createInvoice(payload, { finalize = false } = {}) {
  validateDiscounts(payload);
  const data = await apiFetch('POST', '/client_invoices', { body: payload });
  let invoice = data.client_invoice ?? data;
  if (finalize) return finalizeInvoice(invoice.id);
  return invoice;
}

export async function updateInvoice(id, patch) {
  const current = await retrieveInvoice(id);
  if (current.status && current.status !== 'draft') {
    throw new Error(`Invoice ${current.number ?? id} is ${current.status}, only drafts can be modified.`);
  }
  validateDiscounts({ ...current, ...patch });
  const data = await apiFetch('PUT', `/client_invoices/${id}`, { body: patch });
  return data.client_invoice ?? data;
}

export async function finalizeInvoice(id) {
  await apiFetch('POST', `/client_invoices/${id}/finalize`);
  const full = await retrieveInvoice(id);
  const pdfPath = await downloadInvoicePdf(full);
  return { ...full, pdf_path: pdfPath };
}

export async function sendInvoice(id, { sendTo, emailTitle, emailBody, copyToSelf = true }) {
  if (!Array.isArray(sendTo) || sendTo.length === 0) {
    throw new Error('sendTo must be a non-empty array of email addresses.');
  }
  if (!emailTitle) throw new Error('emailTitle is required.');
  const body = { send_to: sendTo, email_title: emailTitle, copy_to_self: copyToSelf };
  if (emailBody) body.email_body = emailBody;
  return apiFetch('POST', `/client_invoices/${id}/send`, { body });
}

export async function markInvoicePaid(id, { paidAt } = {}) {
  const body = {};
  if (paidAt) body.paid_at = paidAt;
  const data = await apiFetch('POST', `/client_invoices/${id}/mark_as_paid`, { body: Object.keys(body).length ? body : undefined });
  return data.client_invoice ?? data;
}

export async function cancelInvoice(id) {
  const data = await apiFetch('POST', `/client_invoices/${id}/mark_as_canceled`);
  return data.client_invoice ?? data;
}

export async function downloadInvoicePdf(invoice) {
  if (invoice.attachment_id) return downloadAttachmentPdf(invoice.attachment_id);
  if (invoice.pdf_url) return downloadFromUrl(invoice.pdf_url, `${invoice.number ?? invoice.id}.pdf`);
  if (invoice.invoice_url) return downloadFromUrl(invoice.invoice_url, `${invoice.number ?? invoice.id}.pdf`);
  throw new Error('No attachment_id / pdf_url / invoice_url available for this invoice.');
}

function validateDiscounts(payload) {
  if (payload.discount) assertDiscount(payload.discount, 'invoice');
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
