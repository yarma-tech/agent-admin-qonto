import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STATE_PATH = path.resolve(__dirname, '..', 'state.json');

const EMPTY_STATE = { validated_quotes: {} };

export async function readState() {
  try {
    const raw = await fs.readFile(STATE_PATH, 'utf8');
    const parsed = JSON.parse(raw);
    return { ...EMPTY_STATE, ...parsed };
  } catch (err) {
    if (err.code === 'ENOENT') return { ...EMPTY_STATE };
    throw err;
  }
}

export async function writeState(state) {
  const tmp = `${STATE_PATH}.tmp-${process.pid}-${Date.now()}`;
  await fs.writeFile(tmp, JSON.stringify(state, null, 2));
  await fs.rename(tmp, STATE_PATH);
}

export async function recordValidatedQuote(quote, invoice) {
  const state = await readState();
  state.validated_quotes[quote.id] = {
    quote_number: quote.number ?? null,
    validated_at: new Date().toISOString(),
    invoice_id: invoice.id,
    invoice_number: invoice.number ?? null,
  };
  await writeState(state);
  return state.validated_quotes[quote.id];
}
