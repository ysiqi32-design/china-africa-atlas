#!/usr/bin/env python3
"""Bundle JSON datasets into one static JS file for file://, GitHub Pages and offline usage.
Safe: only output from local project JSON; never downloads or executes remote code.
"""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=['worldbank_snapshot','trade','investment','financing','engineering','resources','industry','payments','security','multilateral','society','surveys','external','diplomacy','records','news']
def build():
    result={}
    for name in FILES:
        obj=json.loads((ROOT/'data'/f'{name}.json').read_text(encoding='utf-8'))
        result[name]=obj
    code='/* Generated. Do not edit manually. Regenerate with python scripts/build_bundle.py */\nwindow.ATLAS_DATA_BUNDLE='+json.dumps(result,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'
    target=ROOT/'data'/'bundle.js';target.write_text(code,encoding='utf-8')
    print('Wrote',target,'bytes',len(code.encode('utf-8')))
if __name__=='__main__':build()
