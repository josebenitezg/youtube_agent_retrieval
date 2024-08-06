from typing import List, Dict, Any
from abc import ABC, abstractmethod
import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.tools.retriever import create_retriever_tool
from langchain.tools import BaseTool, tool
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_tool_calling_agent

# Configuration
# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
CHROMA_PERSIST_DIRECTORY = 'db'

class LLMFactory:
    @staticmethod
    def create_llm(provider: str, model: str):
        if provider == "openai":
            return ChatOpenAI(model=model, openai_api_key=OPENAI_API_KEY)
        elif provider == "anthropic":
            return ChatAnthropic(model=model, anthropic_api_key=ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

class VectorStore(ABC):
    @abstractmethod
    def as_retriever(self, **kwargs):
        pass

    @abstractmethod
    def similarity_search_with_score(self, query: str, k: int):
        pass

class ChromaVectorStore(VectorStore):
    def __init__(self, persist_directory: str, embedding_function):
        self.db = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)

    def as_retriever(self, **kwargs):
        return self.db.as_retriever(**kwargs)

    def similarity_search_with_score(self, query: str, k: int):
        return self.db.similarity_search_with_score(query, k=k)

class ToolFactory:
    @staticmethod
    def create_retriever_tool(retriever):
        return create_retriever_tool(
            retriever,
            name="youtube_video_retriever",
            description='''
                        This tool retrieves relevant scientific documents from transcribed YouTube videos based on the user's query. 
                        Use this tool to provide the user with concise and accurate information extracted from these videos. 
                        Limit your response to a maximum of 3 sentences, ensuring precision and relevance to the user's query.
                        '''
        )

    @staticmethod
    @tool
    def get_hubi_eventos():
        '''This us a tool that provides information about the events happening at Huberman Lab.
        '''
        return '''
            Tool en construcción
            '''

    @staticmethod
    @tool
    def other_tool():
        '''Use when provider put something about sports
        '''
        return '''
            Idk. Just kidding, still WIP.
            '''

class PromptBuilder:
    @staticmethod
    def build_contextualize_prompt():
        system_prompt = """
            Given a chat history and the user's most recent question, which may reference the context in the chat history,
            formulate an independent question that can be understood without the chat history.
            """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

    @staticmethod
    def build_qa_prompt():
        system_prompt = """
            You are HubeGPT, a friendly AI assistant that helps people with their questions and concerns about science.
            You are very friendly, care about people's well-being, and like to use emojis.
            Use the information provided in the chat history to give a helpful and accurate response to the user's question.
            """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder('agent_scratchpad')
        ])

class HubeGPT:
    def __init__(self, provider: str, model: str):
        self.embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
        self.vector_store = ChromaVectorStore(CHROMA_PERSIST_DIRECTORY, self.embedding_model)
        self.llm = LLMFactory.create_llm(provider, model)
        self.retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()
        self.chat_history_store: Dict[str, ChatMessageHistory] = {}

    def _setup_tools(self) -> List[BaseTool]:
        tool_factory = ToolFactory()
        return [
            tool_factory.create_retriever_tool(self.retriever),
            tool_factory.get_hubi_eventos,
            tool_factory.other_tool
        ]

    def _setup_agent(self) -> AgentExecutor:
        prompt_builder = PromptBuilder()
        contextualize_prompt = prompt_builder.build_contextualize_prompt()
        qa_prompt = prompt_builder.build_qa_prompt()

        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_prompt
        )

        #agent = create_openai_tools_agent(self.llm, self.tools, qa_prompt)
        agent = create_tool_calling_agent(self.llm, self.tools, qa_prompt)
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, return_intermediate_steps=True)

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.chat_history_store:
            self.chat_history_store[session_id] = ChatMessageHistory()
        return self.chat_history_store[session_id]

    def agent_runner(self):
        return RunnableWithMessageHistory(
            self.agent_executor,
            self.get_session_history,
            input_messages_key="input",
            output_messages_key="output",
            history_messages_key="chat_history",
        )

    def get_relevant_documents(self, query: str):
        return self.vector_store.similarity_search_with_score(query, k=6)

# Usage

# OpenAI configuration
#openai_hubegpt = HubeGPT(provider="openai", model="gpt-4")

# Anthropic configuration
#anthropic_hubegpt = HubeGPT(provider="anthropic", model="claude-3-sonnet-20240320")

# async def astream_agent(input_text: str, session_id: str):
#     log_patches = openai_hubegpt.agent_runner().astream_log(
#         {"input": input_text},
#         config={"configurable": {"session_id": session_id}}
#     )
#     messages = []

#     async for log_patch in log_patches:
#         for op in log_patch.ops:
#             if op['op'] == 'add' and 'value' in op and isinstance(op['value'], AIMessageChunk):
#                 chunk_content = op['value'].content
#                 if chunk_content:
#                     messages.append(chunk_content)
#                     print(f'{chunk_content}', end='', flush=True)

#     return messages

# async def main():
#     input_text = "holaaa como estas?"
#     session_id = "abc123"

#     messages = await astream_agent(input_text, session_id)
#     documents = casa_gpt.get_relevant_documents(input_text)
#     urls = [doc[0].metadata["url"] for doc in documents if "url" in doc[0].metadata]
    
#     print("\nRelevant URLs:", urls)

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())