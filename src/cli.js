#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { ping } from './qonto.js';
import * as clients from './clients.js';
import * as products from './products.js';
import * as quotes from './quotes.js';
import * as invoices from './invoices.js';
import { validateQuote } from './validate.js';
import { pendingPayments } from './reports.js';

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const eq = arg.indexOf('=');
      if (eq !== -1) {
        args[arg.slice(2, eq)] = arg.slice(eq + 1);
      } else {
        const next = argv[i + 1];
        if (next && !next.startsWith('--')) {
          args[arg.slice(2)] = next;
          i += 1;
        } else {
          args[arg.slice(2)] = true;
        }
      }
    } else {
      args._.push(arg);
    }
  }
  return args;
}

async function readJsonArg(args) {
  if (!args.json) throw new Error('Missing --json <path>.');
  const absolute = path.resolve(process.cwd(), args.json);
  const raw = await fs.readFile(absolute, 'utf8');
  return JSON.parse(raw);
}

function out(result) {
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

function die(err) {
  process.stderr.write(`${err.message ?? err}\n`);
  process.exit(1);
}

const commands = {
  async ping() {
    out(await ping());
  },

  async 'client-list'(args) {
    out(await clients.listClients({ type: args.type, limit: args.limit ? Number(args.limit) : undefined }));
  },
  async 'client-find'(args) {
    const query = args._[0];
    if (!query) throw new Error('client-find requires a search term.');
    out(await clients.findClients(query));
  },
  async 'client-get'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await clients.retrieveClient(args.id));
  },
  async 'client-create'(args) {
    out(await clients.createClient(await readJsonArg(args)));
  },
  async 'client-update'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await clients.updateClient(args.id, await readJsonArg(args)));
  },

  async 'product-list'(args) {
    out(await products.listProducts({ limit: args.limit ? Number(args.limit) : undefined }));
  },
  async 'product-find'(args) {
    const query = args._[0];
    if (!query) throw new Error('product-find requires a search term.');
    out(await products.findProducts(query));
  },
  async 'product-get'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await products.retrieveProduct(args.id));
  },
  async 'product-create'(args) {
    out(await products.createProduct(await readJsonArg(args)));
  },
  async 'product-update'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await products.replaceProduct(args.id, await readJsonArg(args)));
  },
  async 'product-delete'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await products.deleteProduct(args.id));
  },

  async 'quote-list'(args) {
    out(await quotes.listQuotes({
      clientId: args['client-id'],
      from: args.from,
      to: args.to,
      limit: args.limit ? Number(args.limit) : undefined,
    }));
  },
  async 'quote-find'(args) {
    const term = args._[0];
    if (!term) throw new Error('quote-find requires a search term.');
    out(await quotes.findQuotes(term));
  },
  async 'quote-get'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await quotes.retrieveQuote(args.id));
  },
  async 'quote-create'(args) {
    out(await quotes.createQuote(await readJsonArg(args)));
  },
  async 'quote-update'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await quotes.updateQuote(args.id, await readJsonArg(args)));
  },
  async 'quote-send'(args) {
    if (!args.id) throw new Error('Missing --id.');
    const payload = await readJsonArg(args);
    out(await quotes.sendQuote(args.id, {
      sendTo: payload.send_to ?? payload.sendTo,
      emailTitle: payload.email_title ?? payload.emailTitle,
      emailBody: payload.email_body ?? payload.emailBody,
      copyToSelf: payload.copy_to_self ?? payload.copyToSelf ?? true,
    }));
  },
  async 'quote-validate'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await validateQuote(args.id, { dueDate: args['due-date'] }));
  },

  async 'invoice-list'(args) {
    out(await invoices.listInvoices({
      status: args.status,
      clientId: args['client-id'],
      from: args.from,
      to: args.to,
      limit: args.limit ? Number(args.limit) : undefined,
    }));
  },
  async 'invoice-find'(args) {
    const term = args._[0];
    if (!term) throw new Error('invoice-find requires a search term.');
    out(await invoices.findInvoices(term));
  },
  async 'invoice-get'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await invoices.retrieveInvoice(args.id));
  },
  async 'invoice-create'(args) {
    const payload = await readJsonArg(args);
    out(await invoices.createInvoice(payload, { finalize: Boolean(args.finalize) }));
  },
  async 'invoice-update'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await invoices.updateInvoice(args.id, await readJsonArg(args)));
  },
  async 'invoice-finalize'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await invoices.finalizeInvoice(args.id));
  },
  async 'invoice-send'(args) {
    if (!args.id) throw new Error('Missing --id.');
    const payload = await readJsonArg(args);
    out(await invoices.sendInvoice(args.id, {
      sendTo: payload.send_to ?? payload.sendTo,
      emailTitle: payload.email_title ?? payload.emailTitle,
      emailBody: payload.email_body ?? payload.emailBody,
      copyToSelf: payload.copy_to_self ?? payload.copyToSelf ?? true,
    }));
  },
  async 'invoice-mark-paid'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await invoices.markInvoicePaid(args.id, { paidAt: args['paid-at'] }));
  },
  async 'invoice-cancel'(args) {
    if (!args.id) throw new Error('Missing --id.');
    out(await invoices.cancelInvoice(args.id));
  },

  async 'pending-payments'(args) {
    out(await pendingPayments({ detailed: Boolean(args.detailed) }));
  },

  async help() {
    const commandNames = Object.keys(commands).sort();
    out({
      usage: 'node src/cli.js <command> [options]',
      commands: commandNames,
      docs: 'https://github.com/yarma-tech/agent-admin-qonto#readme',
    });
  },
};

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  if (!command || command === '--help' || command === '-h') {
    await commands.help();
    return;
  }
  const handler = commands[command];
  if (!handler) {
    die(new Error(`Unknown command: ${command}. Run 'help' to see available commands.`));
    return;
  }
  const args = parseArgs(rest);
  try {
    await handler(args);
  } catch (err) {
    die(err);
  }
}

main();
