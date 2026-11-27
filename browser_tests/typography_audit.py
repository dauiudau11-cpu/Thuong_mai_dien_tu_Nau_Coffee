"""Visual-only typography evidence; optional installed Windows Georgia is never bundled."""
import base64
from pathlib import Path


def install_windows_georgia(context):
    faces=[]
    for weight,name in [(400,'georgia.ttf'),(700,'georgiab.ttf')]:
        p=Path('/mnt/c/Windows/Fonts')/name
        if p.is_file():
            data=base64.b64encode(p.read_bytes()).decode()
            faces.append(f"new FontFace('Georgia','url(data:font/ttf;base64,{data})',{{weight:'{weight}'}}).load().then(f=>document.fonts.add(f))")
    if faces:
        context.add_init_script('window.nauInstalledGeorgia = Promise.all(['+','.join(faces)+']);')
    return bool(faces)


def audit_page(page,strict):
    page.evaluate('async()=>{await window.nauInstalledGeorgia;await document.fonts.ready;}')
    session=page.context.new_cdp_session(page);session.send('DOM.enable');session.send('CSS.enable')
    root=session.send('DOM.getDocument')['root']['nodeId'];nodes=session.send('DOM.querySelectorAll',{'nodeId':root,'selector':'h1,h2,h3,h4'})['nodeIds'][:10]
    evidence=[]
    for node in nodes:
        obj=session.send('DOM.resolveNode',{'nodeId':node})['object']['objectId']
        data=session.send('Runtime.callFunctionOn',{'objectId':obj,'functionDeclaration':'''function(){const s=getComputedStyle(this);return {text:this.textContent.trim(),family:s.fontFamily,weight:s.fontWeight,tracking:s.letterSpacing,wordSpacing:s.wordSpacing,kerning:s.fontKerning,features:s.fontFeatureSettings,textRendering:s.textRendering,nfc:this.textContent===this.textContent.normalize('NFC'),visible:!!this.getClientRects().length};}''','returnByValue':True})['result']['value']
        if not data['visible'] or not data['text']:continue
        data['fonts']=session.send('CSS.getPlatformFontsForNode',{'nodeId':node})['fonts']
        if strict:
            assert any(name in data['family'] for name in ['Noto Serif','Be Vietnam Pro']),data
            # Icon glyphs may intentionally fall back; Vietnamese heading letters may not.
            has_icon=any(ord(c)>0x21ff for c in data['text'])
            if not has_icon:
                assert all(f['isCustomFont'] and f['postScriptName'].split('-')[0] in ['NotoSerif','BeVietnamPro'] for f in data['fonts']),data
        evidence.append(data)
    session.detach();return evidence
