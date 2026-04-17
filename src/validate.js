import { retrieveQuote } from './quotes.js';
import { createInvoice } from './invoices.js';
import { recordValidatedQuote } from './state.js';

export async function validateQuote(quoteId, { dueDate } = {}) {
  const quote = await retrieveQuote(quoteId);

  const clientId = quote.client?.id ?? quote.client_id;
  if (!clientId) throw new Error(`Quote ${quoteId} has no client reference.`);

  const issueDate = new Date().toISOString().slice(0, 10);
  const computedDue = dueDate ?? addDays(issueDate, 30);

  const invoicePayload = {
    client_id: clientId,
    issue_date: issueDate,
    due_date: computedDue,
    currency: quote.currency ?? 'EUR',
    items: (quote.items ?? []).map(stripServerFields),
    purchase_order: quote.purchase_order ?? undefined,
    header: quote.header ?? undefined,
    footer: quote.footer ?? undefined,
  };
  if (quote.discount) invoicePayload.discount = quote.discount;
  if (quote.terms_and_conditions) invoicePayload.terms_and_conditions = quote.terms_and_conditions;

  const invoice = await createInvoice(invoicePayload);
  const mapping = await recordValidatedQuote(quote, invoice);

  return { quote_id: quote.id, quote_number: quote.number, invoice, mapping };
}

function stripServerFields(item) {
  const { id, created_at, updated_at, ...clean } = item;
  return clean;
}

function addDays(isoDate, days) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}
