#!/usr/bin/env python3
"""Build a self-contained review HTML, optionally updating Markdown sources."""
import argparse
import copy
import hashlib
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace', type=Path, default=ROOT / 'workspace.json')
parser.add_argument('--docs', type=Path, nargs='*', default=[])
parser.add_argument('--output', type=Path, default=ROOT / 'index.html')
parser.add_argument('--title')
parser.add_argument('--new', action='store_true', help='Create a fresh workspace from --docs')
args = parser.parse_args()
if args.new:
    if not args.docs:
        parser.error('--new requires at least one Markdown file via --docs')
    state = {'format': 'agent-docs-workspace', 'version': 1, 'id': str(uuid.uuid4()),
             'title': args.title or '文档评审', 'generation': 0,
             'documents': [], 'threads': [], 'appliedChangeIds': []}
else:
    state = json.loads(args.workspace.read_text())
    if state.get('format') != 'agent-docs-workspace' or state.get('version') != 1:
        parser.error('Expected an exported agent-docs-workspace version 1 JSON file')
state = copy.deepcopy(state)
if args.title:
    state['title'] = args.title
seen = set()
for path in args.docs:
    source = path.name
    if source in seen:
        parser.error('Markdown filenames must be unique: ' + source)
    seen.add(source)
    markdown = path.read_text()
    doc = next((d for d in state['documents'] if d.get('source') == source), None)
    if doc:
        if doc['markdown'] != markdown:
            doc['markdown'] = markdown
            doc['revision'] += 1
    else:
        state['documents'].append({
            'id': 'doc-' + hashlib.sha256(source.encode()).hexdigest()[:16],
            'source': source, 'title': path.stem, 'kind': 'DOC',
            'revision': 1, 'markdown': markdown,
        })
state['generation'] = state.get('generation', 0) + 1
# Escape script terminators even when documents contain literal HTML/script examples.
payload = json.dumps(state, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
html = (ROOT / 'template.html').read_text()
html = html.replace('/*__VENDOR__*/', (ROOT / '.vendor.js').read_text())
html = html.replace('__WORKSPACE_JSON__', payload)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(html)
print(f'Created {args.output} ({args.output.stat().st_size:,} bytes)')
