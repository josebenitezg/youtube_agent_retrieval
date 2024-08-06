from fasthtml.common import *
from utils.youtube_utils import YouTubeThumbnail

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
                 placeholder="AMA...", 
                 cls="input input-bordered w-full", hx_swap_oob='true')