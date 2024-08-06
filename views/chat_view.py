from fasthtml.common import *
from config import app
from models.chat_model import ChatModel
from views.components import ChatMessage, ChatInput
import uuid
import asyncio

chat_model = ChatModel()

@app.route("/")
def get(session):
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    messages = chat_model.get_messages(session['session_id'])
    
    page = Body(
        H1('HubeGPT. Hubermanlab podcast Agent Retrieval'),
        Div(*[ChatMessage(i, messages) for i in range(len(messages))],
            id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
        Form(Group(ChatInput(), Button("Send", cls="btn btn-primary bg-blue-500 hover:bg-blue-600 text-white")),
            ws_send=session['session_id'], hx_ext="ws", ws_connect="/wscon",
            cls="flex space-x-2 mt-2",
        ), 
        cls="p-4 max-w-lg mx-auto",
    )
    return Title('HubiGPT'), page

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
        
    documents = chat_model.get_relevant_documents(messages[-2]["content"])
    urls = [doc[0].metadata["url"] for doc in documents if "url" in doc[0].metadata]
    chat_model.add_context_to_last_message(session_id, urls)
    
    if messages[-1]["context"]:
        await send(Div(ChatMessage(len(messages)-1, messages), hx_swap_oob='outerHTML', id=f"chat-message-{len(messages)-1}"))
    
    await send(Script("scrollToBottom();"))