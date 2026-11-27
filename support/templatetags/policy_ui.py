import re
from urllib.parse import urlsplit
from django import template
from catalog.store_identity import STORE
register=template.Library()

@register.simple_tag
def store_identity():return STORE

@register.filter
def policy_blocks(body):
    def safe_link(value):
        try:parsed=urlsplit(value.strip())
        except (TypeError,ValueError):return ''
        return value.strip() if parsed.scheme in ('http','https','mailto','tel') else ''
    token=re.compile(r'(\*\*[^*\n]+\*\*|(?<!\*)\*[^*\n]+\*(?!\*)|\[[^\]\n]+\]\([^\s)]+\))')
    def inline(value):
        result=[];position=0
        for match in token.finditer(value):
            if match.start()>position:result.append({'kind':'text','text':value[position:match.start()]})
            part=match.group(0)
            if part.startswith('**'):result.append({'kind':'strong','text':part[2:-2]})
            elif part.startswith('*'):result.append({'kind':'em','text':part[1:-1]})
            else:
                label,url=re.match(r'^\[([^]]+)\]\(([^)]+)\)$',part).groups();url=safe_link(url)
                result.append({'kind':'link' if url else 'text','text':label,'url':url})
            position=match.end()
        if position<len(value):result.append({'kind':'text','text':value[position:]})
        return result or [{'kind':'text','text':''}]
    blocks=[];lines=body.splitlines();index=0;paragraph=[]
    def flush():
        if paragraph:
            blocks.append({'kind':'paragraph','content':inline(' '.join(paragraph))});paragraph.clear()
    while index<len(lines):
        line=lines[index].strip()
        if not line:flush();index+=1;continue
        if line.startswith('### '):flush();blocks.append({'kind':'h3','content':inline(line[4:])});index+=1;continue
        if line.startswith('## '):flush();blocks.append({'kind':'h2','content':inline(line[3:])});index+=1;continue
        if line.startswith('**') and line.endswith('**') and line.count('**')==2:
            flush();blocks.append({'kind':'h2','content':inline(line[2:-2])});index+=1;continue
        if line.startswith('- '):
            flush();items=[]
            while index<len(lines) and lines[index].strip().startswith('- '):
                items.append(inline(lines[index].strip()[2:]));index+=1
            blocks.append({'kind':'list','items':items});continue
        if re.match(r'^\d+\. ',line):
            flush();items=[]
            while index<len(lines) and re.match(r'^\d+\. ',lines[index].strip()):
                items.append(inline(re.sub(r'^\d+\. ','',lines[index].strip())));index+=1
            blocks.append({'kind':'ordered','items':items});continue
        paragraph.append(line);index+=1
    flush()
    return blocks
