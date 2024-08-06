from fasthtml.common import *

with open("./static/js/auto_scroll.js", 'r') as file:
    js_content = file.read()
    
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
auto_scroll_script = Script(js_content)

app = FastHTML(hdrs=(tlink, dlink, picolink, auto_scroll_script), ws_hdr=True)