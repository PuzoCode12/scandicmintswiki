import json, re, sys, os
from PIL import Image

src_json, photos_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
TR = dict(zip('абвгдежзийклмнопрстуфхцчшщъыьэюя', ['a','b','v','g','d','e','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','c','ch','sh','sch','','y','','e','yu','ya']))

def slugify(s):
    s = ''.join(TR.get(c, c) for c in s.lower().replace('ё', 'e'))
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')[:60]

def md_escape(t):
    return re.sub(r'([*_\[\]])', r'\\\1', t)

def wrap(t, mark):
    out_parts = []
    for part in re.split(r'(\n+)', t):
        if part.strip() and not part.startswith('\n'):
            lead = part[:len(part) - len(part.lstrip())]
            trail = part[len(part.rstrip()):]
            out_parts.append(lead + mark + part.strip() + mark + trail)
        else:
            out_parts.append(part)
    return ''.join(out_parts)

def to_md(entities):
    res = ''
    for e in entities:
        t, k = e['text'], e['type']
        if k == 'bold': res += wrap(md_escape(t), '**')
        elif k == 'italic': res += wrap(md_escape(t), '*')
        elif k == 'text_link': res += '[' + md_escape(t) + '](' + e['href'] + ')'
        elif k == 'blockquote': res += '\n'.join('> ' + l for l in t.split('\n'))
        else: res += md_escape(t)
    res = re.sub(r'[\ufffc\u200b]', '', res)
    lines = [l.rstrip() for l in res.split('\n')]
    lines = [l for l in lines if not re.fullmatch(r'[\s]*', l) or l == '']
    paras, cur = [], []
    for l in lines:
        if l == '':
            if cur: paras.append(cur); cur = []
        else:
            cur.append(re.sub(r'^#', r'\\#', l.strip()))
    if cur: paras.append(cur)
    return '\n\n'.join('  \n'.join(p) for p in paras)

def plain(entities):
    return re.sub(r'[\ufffc\u200b]', '', ''.join(e['text'] for e in entities)).strip()

def convert(name):
    dest = os.path.join(out, 'public', 'photos', name.rsplit('.', 1)[0].replace('@', '-') + '.webp')
    srcp = os.path.join(photos_dir, name)
    if not os.path.exists(srcp): return None
    if not os.path.exists(dest):
        im = Image.open(srcp).convert('RGB')
        im.thumbnail((900, 900))
        im.save(dest, 'WEBP', quality=80)
    return '/photos/' + os.path.basename(dest)

msgs = [m for m in json.load(open(src_json, encoding='utf-8'))['messages'] if m['type'] == 'message' and 'photo' in m]
os.makedirs(os.path.join(out, 'public', 'photos'), exist_ok=True)
os.makedirs(os.path.join(out, 'src', 'content', 'candies'), exist_ok=True)
entries = []
for m in msgs:
    ents = m.get('text_entities') or []
    img = convert(os.path.basename(m['photo']))
    if not plain(ents):
        if entries and img: entries[-1]['photos'].append(img)
        continue
    entries.append({'id': m['id'], 'date': m['date'][:10], 'ents': ents, 'photos': [img] if img else []})

used = set()
for e in entries:
    txt = plain(e['ents'])
    title = txt.split('\n')[0].strip().lstrip('#').strip()
    first = title.split()[0] if title else ''
    brand = 'Polar Express' if title.startswith('Polar Express') else ('Scandic' if 'Scandic' in title else 'Другие производители')
    line = (re.search(r'Линейка:\s*([^\n]+)', txt) or [None, ''])[1].strip()
    fl = re.search(r'Вкус[ы]?:\s*([^\n]+)', txt)
    flavors = [f.strip(' .') for f in re.split(r',| и ', fl.group(1)) if f.strip(' .')] if fl else []
    slug = slugify(title) or str(e['id'])
    if slug in used: slug += '-' + str(e['id'])
    used.add(slug)
    q = lambda s: json.dumps(s, ensure_ascii=False)
    fm = ['---', 'title: ' + q(title), 'brand: ' + q(brand), 'line: ' + q(line), 'flavors: ' + q(flavors), 'collection: ""', 'date: ' + e['date'], 'photos: ' + q(e['photos']), '---', '']
    body = to_md(e['ents'])
    open(os.path.join(out, 'src', 'content', 'candies', slug + '.md'), 'w', encoding='utf-8').write('\n'.join(fm) + body + '\n')
print(len(entries), 'entries')
