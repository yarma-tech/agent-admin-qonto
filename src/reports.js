import { listInvoices, retrieveInvoice } from './invoices.js';
import { listQuotes } from './quotes.js';
import { readState } from './state.js';

export async function pendingPayments({ detailed = false } = {}) {
  const [unpaidInvoices, allQuotes, state] = await Promise.all([
    listInvoices({ status: 'unpaid', limit: 500 }),
    listQuotes({ limit: 500 }),
    readState(),
  ]);

  const byClient = new Map();
  let total = 0;
  const invoicesDetail = [];
  const quotesDetail = [];

  for (const inv of unpaidInvoices) {
    const amount = toAmount(inv.total_amount?.value ?? inv.amount?.value ?? 0);
    total += amount;
    bump(byClient, inv.client?.name ?? inv.client_id ?? 'unknown', amount);
    if (detailed) invoicesDetail.push(summarizeInvoice(inv, amount));
  }

  const validated = state.validated_quotes ?? {};
  const paidInvoiceIds = new Set();
  for (const [, mapping] of Object.entries(validated)) {
    if (!mapping.invoice_id) continue;
    try {
      const inv = await retrieveInvoice(mapping.invoice_id);
      if (inv.status === 'paid' || inv.status === 'canceled') paidInvoiceIds.add(mapping.invoice_id);
    } catch {
      // ignore — mapping may reference a deleted invoice
    }
  }

  for (const q of allQuotes) {
    const mapping = validated[q.id];
    if (!mapping) continue;
    if (paidInvoiceIds.has(mapping.invoice_id)) continue;
    const amount = toAmount(q.total_amount?.value ?? q.amount?.value ?? 0);
    total += amount;
    bump(byClient, q.client?.name ?? q.client_id ?? 'unknown', amount);
    if (detailed) quotesDetail.push(summarizeQuote(q, amount, mapping));
  }

  return {
    total: total.toFixed(2),
    currency: 'EUR',
    by_client: [...byClient.entries()]
      .map(([name, amount]) => ({ name, amount: amount.toFixed(2) }))
      .sort((a, b) => Number(b.amount) - Number(a.amount)),
    by_source: {
      unpaid_invoices_count: unpaidInvoices.length,
      validated_quotes_pending_count: detailed ? quotesDetail.length : undefined,
    },
    ...(detailed ? { invoices: invoicesDetail, quotes: quotesDetail } : {}),
  };
}

function toAmount(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function bump(map, key, amount) {
  map.set(key, (map.get(key) ?? 0) + amount);
}

function summarizeInvoice(inv, amount) {
  return {
    id: inv.id,
    number: inv.number,
    client: inv.client?.name,
    amount: amount.toFixed(2),
    issue_date: inv.issue_date,
    due_date: inv.due_date,
  };
}

function summarizeQuote(q, amount, mapping) {
  return {
    id: q.id,
    number: q.number,
    client: q.client?.name,
    amount: amount.toFixed(2),
    validated_at: mapping.validated_at,
    invoice_id: mapping.invoice_id,
  };
}
