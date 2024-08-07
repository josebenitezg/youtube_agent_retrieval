from agents.agent_retriever import HubeGPT
from langchain_core.messages import AIMessageChunk

# PROVIDER = "anthropic"
# MODEL = "claude-3-5-sonnet-20240620"

PROVIDER = "openai"
MODEL = "gpt-4o"

hubegpt = HubeGPT(provider=PROVIDER, model=MODEL)

class ChatModel:
    def __init__(self):
        self.sessions = {}
        self.hubegpt = hubegpt.agent_runner()

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
                print(op)
                if op['op'] == 'add' and 'value' in op and isinstance(op['value'], AIMessageChunk):
                    if PROVIDER == "anthropic":
                        # Handle Anthropic response
                        if isinstance(op['value'].content, list) and op['value'].content:
                            chunk_content = op['value'].content[0].get('text', '')
                        else:
                            chunk_content = ''
                    else:
                        # Handle OpenAI response
                        chunk_content = op['value'].content
                        
                    if chunk_content:
                        self.sessions[session_id][-1]["content"] += chunk_content
                        yield chunk_content

    def get_relevant_documents(self, content):
        return hubegpt.get_relevant_documents(content)
    
# chatanthropic 
# {'op': 'add', 'path': '/logs/ChatAnthropic/streamed_output/-', 'value': AIMessageChunk(content=[{'text': 'Hello there', 'type': 'text', 'index': 0}], id='run-d450be24-70fc-4dbe-b203-5860a32c7112')}
# chatopenai
# {'op': 'add', 'path': '/logs/ChatOpenAI/streamed_output/-', 'value': AIMessageChunk(content='Hello', id='run-40b754c5-6201-4ba5-b702-78aa94fccd36')}