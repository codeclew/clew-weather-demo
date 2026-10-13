import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

class Element {
  constructor(tag, document) {
    this.tagName = tag;
    this.document = document;
    this.children = [];
    this.dataset = {};
    this.style = {};
    this.textContent = '';
  }
  append(...children) { this.children.push(...children); }
  contains(element) { return this === element || this.children.some(child => child.contains(element)); }
  replaceChildren(...children) {
    if (this.contains(this.document.activeElement)) this.document.activeElement = this.document.body;
    this.children = children;
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => [
      ...(selector === '[data-refresh]' && child.dataset.refresh ? [child] : []),
      ...child.querySelectorAll(selector),
    ]);
  }
  focus() { this.document.activeElement = this; }
}
const document = {};
document.body = new Element('body', document);
document.activeElement = document.body;
const cards = new Element('section', document);
const status = new Element('p', document);
document.createElement = tag => new Element(tag, document);
document.querySelector = selector => selector === '#cards' ? cards : status;
document.querySelectorAll = () => [];
let rows = [{ id: 'oslo', name: 'Oslo', forecast: null }];
let poll;
const context = vm.createContext({ document, fetch: async () => ({ ok: true, json: async () => rows }), setInterval: callback => { poll = callback; } });
const html = readFileSync(new URL('../services/dashboard/public/index.html', import.meta.url), 'utf8');
vm.runInContext(html.match(/<script>([\s\S]*)<\/script>/)[1], context);
await vm.runInContext('update()', context);
const button = cards.querySelectorAll('[data-refresh]')[0];
button.focus();
await poll();
assert.equal(document.activeElement, button, 'unchanged polling preserves focused button');
assert.equal(cards.querySelectorAll('[data-refresh]')[0], button, 'unchanged polling retains card controls');
rows = [{ ...rows[0], name: 'Oslo updated' }];
await poll();
const replacement = cards.querySelectorAll('[data-refresh]')[0];
assert.notEqual(replacement, button);
assert.equal(document.activeElement, replacement, 'changed data restores focus to the same city action');
const outside = new Element('button', document);
outside.focus();
rows = [{ ...rows[0], name: 'Oslo updated again' }];
await poll();
assert.equal(document.activeElement, outside, 'polling does not steal focus from outside cards');
rows = [];
await poll();
assert.equal(status.textContent, 'Choose a city');
console.log('Dashboard focus regression: 6 assertions passed');
