from fasthtml.common import *
import asyncio
from agents.agent_retriever import HubeGPT
from langchain_core.messages import AIMessageChunk
import uuid

hubegpt = HubeGPT()

auto_scroll_script = Script("""
function scrollToBottom() {
    const chatlist = document.getElementById('chatlist');
    if (chatlist) {
        chatlist.scrollTop = chatlist.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const chatlist = document.getElementById('chatlist');
    if (chatlist) {
        // Initial scroll
        scrollToBottom();

        // Set up MutationObserver
        const observer = new MutationObserver(scrollToBottom);
        observer.observe(chatlist, { childList: true, subtree: true });

        // Listen for HTMX events
        document.body.addEventListener('htmx:afterOnLoad', scrollToBottom);
        document.body.addEventListener('htmx:wsAfterMessage', scrollToBottom);
    }
});

// Expose the function for global use
window.scrollToBottom = scrollToBottom;
""")


def YouTubeThumbnail(url):
    video_id = url.split("v=")[-1]
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
    return Div(
        A(Img(src=thumbnail_url, alt="YouTube Thumbnail", cls="w-full h-auto object-cover"),
          href=url, target="_blank", rel="noopener noreferrer"),
        cls="w-1/2 sm:w-1/3 md:w-1/3 p-1"
    )

def create_context_accordion(msg_idx, context):
    return Div(
        Div(
            Input(type="checkbox", id=f"accordion-check-{msg_idx}", cls="peer hidden"),
            Label("Sources", fr=f"accordion-check-{msg_idx}", 
                  cls="block cursor-pointer bg-gray-100 p-2 rounded-t peer-checked:rounded-b-none text-sm mt-2 text-gray-600"),
            Div(
                Div(*[YouTubeThumbnail(url) for url in context],
                    cls="flex flex-wrap -mx-1 mt-2"),
                cls="hidden peer-checked:block bg-gray-50 p-2 rounded-b overflow-auto max-h-64 absolute left-0 right-0 z-10"
            ),
            cls="w-full relative"
        ),
        id=f"context-accordion-{msg_idx}",
        cls="mt-2"
    )

def ChatMessage(msg_idx, messages):
    msg = messages[msg_idx]
    is_user = msg['role'] == 'user'
    #bubble_class = f"chat-bubble-{'primary' if is_user else 'secondary'}"
    bubble_class = "bg-white text-gray-800 border border-gray-200"
    chat_class = f"chat-{'end' if is_user else 'start'}"
    
    display_role = "HubeGPT" if msg['role'] == 'assistant' else msg['role']
    
    content = [
        Div(display_role, cls="chat-header"),
        Div(msg['content'], 
            id=f"chat-content-{msg_idx}",
            cls=f"chat-bubble {bubble_class} whitespace-pre-wrap")
    ]
    
    if not is_user and 'context' in msg and msg['context']:
        accordion = create_context_accordion(msg_idx, msg['context'])
        content.append(accordion)
    
    message_content = Div(*content, cls="message-content")
    return Div(message_content,
               id=f"chat-message-{msg_idx}",
               cls=f"chat {chat_class} mb-8 relative")

def ChatInput():
    return Input(type="text", name='msg', id='msg-input', 
                 placeholder="Preguntame algo...", 
                 cls="input input-bordered w-full", hx_swap_oob='true')

class ChatModel:
    def __init__(self):
        self.sessions = {}
        self.hubegpt = hubegpt.casa_chain()

    def get_messages(self, session_id):
        return self.sessions.get(session_id, [])

    def add_user_message(self, session_id, content):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": "user", "content": content})

    def add_assistant_message(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": "assistant", "content": "", "context": []})

    def add_context_to_last_message(self, session_id, urls):
        if session_id in self.sessions and self.sessions[session_id]:
            self.sessions[session_id][-1]["context"] = urls

    async def stream_response(self, session_id):
        messages = self.get_messages(session_id)
        input_text = messages[-2]["content"] if len(messages) > 1 and messages[-2]['role'] == 'user' else ""
        
        async for log_patch in self.hubegpt.astream_log({"input": input_text}, config={"configurable": {"session_id": session_id}}):
            for op in log_patch.ops:
                if op['op'] == 'add' and 'value' in op and isinstance(op['value'], AIMessageChunk):
                    chunk_content = op['value'].content
                    if chunk_content:
                        self.sessions[session_id][-1]["content"] += chunk_content
                        yield chunk_content

# Configuración de la aplicación
tlink = Script(src="https://cdn.tailwindcss.com")
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
app = FastHTML(hdrs=(tlink, dlink, picolink, auto_scroll_script), ws_hdr=True)

chat_model = ChatModel()

@app.route("/")
def get(session):
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    messages = chat_model.get_messages(session['session_id'])
    
    page = Body(
        H1('CasaGPT. Una AI al servicio de Dios y la comunidad'),
        Div(*[ChatMessage(i, messages) for i in range(len(messages))],
            id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
        Form(Group(ChatInput(), Button("Send", cls="btn btn-primary bg-blue-500 hover:bg-blue-600 text-white")),
            ws_send=session['session_id'], hx_ext="ws", ws_connect="/wscon",
            cls="flex space-x-2 mt-2",
        ), 
        cls="p-4 max-w-lg mx-auto",
    )
    return Title('CasaGPT'), page

@app.ws('/wscon')
async def ws(msg: str, send, ws):
    session_id = ws.session_id if hasattr(ws, 'session_id') else None
    if not session_id:
        ws.session_id = str(uuid.uuid4())
        await send("Session established")
        return

    await handle_user_message(msg, send, ws.session_id)
    await process_assistant_response(send, ws.session_id)

async def handle_user_message(msg: str, send, session_id: str):
    chat_model.add_user_message(session_id, msg)
    messages = chat_model.get_messages(session_id)
    await send(Div(ChatMessage(len(messages)-1, messages), hx_swap_oob='beforeend', id="chatlist"))
    await send(ChatInput())
    await send(Script("scrollToBottom();"))

async def process_assistant_response(send, session_id: str):
    chat_model.add_assistant_message(session_id)
    messages = chat_model.get_messages(session_id)
    await send(Div(ChatMessage(len(messages)-1, messages), hx_swap_oob='beforeend', id="chatlist"))
    await send(Script("scrollToBottom();"))

    async for chunk in chat_model.stream_response(session_id):
        await send(Span(chunk, id=f"chat-content-{len(messages)-1}", hx_swap_oob="beforeend"))
        await asyncio.sleep(0.01)
        
    documents = hubegpt.get_relevant_documents(messages[-2]["content"])
    urls = [doc[0].metadata["url"] for doc in documents if "url" in doc[0].metadata]
    chat_model.add_context_to_last_message(session_id, urls)
    
    if messages[-1]["context"]:
        await send(Div(ChatMessage(len(messages)-1, messages), hx_swap_oob='outerHTML', id=f"chat-message-{len(messages)-1}"))
    
    await send(Script("scrollToBottom();"))

# Ejecución de la aplicación
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run("__main__:app", host='0.0.0.0', port=8000, reload=True)
#if __name__ == '__main__': uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
serve()