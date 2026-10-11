#!/usr/bin/env python3
"""Create stand-alone file:// compatible HTML with all JS/CSS and static data inline."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text(encoding='utf-8')
css=(ROOT/'style.css').read_text(encoding='utf-8')
js=(ROOT/'app.js').read_text(encoding='utf-8')
upload=(ROOT/'upload.js').read_text(encoding='utf-8')
bundle=(ROOT/'data'/'bundle.js').read_text(encoding='utf-8')
html=html.replace('<link rel="stylesheet" href="./style.css"/>','<style>\n'+css+'\n</style>')
html=html.replace('<script src="./data/bundle.js"></script>','<script>\n'+bundle+'\n</script>')
html=html.replace('<script src="./upload.js"></script>','<script>\n'+upload.replace('</script','<\\/script')+'\n</script>')
html=html.replace('<script src="./app.js"></script>','<script>\n'+js.replace('</script','<\\/script')+'\n</script>')
out=ROOT.parent/'非洲研究图谱_v2_可直接打开.html';out.write_text(html,encoding='utf-8')
print('Created',out,'bytes',out.stat().st_size)
