# Stephan Raaijmakers, 2024
#!pip install -r /content/drive/MyDrive/CODE/requirements.txt
import os
from langchain.chat_models import ChatOpenAI
from google.colab import userdata
import dotenv
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain import PromptTemplate,HuggingFaceHub
from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import bs4
from chromadb.utils import embedding_functions
from langchain import hub

from langchain_core.prompts import ChatPromptTemplate

from operator import itemgetter

# If you use COLAB: put your Hggingface/OpenAI keys in keys.env, or upload them in COLAB through the "key" icon.
# Otherwise put then in the code (be careful).
dotenv.load_dotenv('/content/drive/MyDrive/CODE/keys.env')

##os.environ["OPENAI_API_KEY"] = userdata.get('OPENAI_API_KEY')
#chat = ChatOpenAI(
#    openai_api_key=os.environ.get("OPENAI_API_KEY"),
#    model='gpt-3.5-turbo'
#)
#os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")


template = """Question: {question}
Let's think step by step. Answer in Dutch.

Answer: """

# https://huggingface.co/spaces/BramVanroy/open_dutch_llm_leaderboard
# OK llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.1, "max_length":64})

llm = HuggingFaceHub(repo_id="HuggingFaceH4/zephyr-7b-beta", model_kwargs={"temperature":0.1,"max_length":128})

# TOO BIG llm = HuggingFaceHub(repo_id="BramVanroy/Llama-2-13b-chat-dutch", model_kwargs={"temperature":0.1,"max_length":64})
# TOO BIG llm = HuggingFaceHub(repo_id="BramVanroy/GEITje-7B-ultra", model_kwargs={"temperature":0.1,"max_length":64})
# OK llm = HuggingFaceHub(repo_id="mistralai/Mistral-7B-v0.1", model_kwargs={"temperature":0.1, "max_length":64})

#prompt = """Question: Can Barack Obama have a conversation with George Washington?

#Let's think step by step.

#Answer: """

#print(llm(prompt))

# ===================================================================


loader = WebBaseLoader(
    web_paths=("<url>",),

    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
            #class_=("content_main")
        )
    ),
)

# Create a folder ./documents, with *.txt files.

docs=[]
n=0
for file in os.listdir("./documents"):
  if file.endswith('.txt'):
    n+=1
    loader=TextLoader("./documents/"+file)
    docs.extend(loader.load())
#docs = loader.load()

print("LOADED ",n, " documents")
print(docs)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

#st_emb = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

#embedding_function = SentenceTransformerEmbeddings(model_name="GroNLP/gpt2-medium-dutch-embeddings")

vectorstore = Chroma.from_documents(documents=splits,embedding=embedding_function)

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")

#llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Replace <query> with your query below:
print("\n================================================================\n")
print("QUERY: <query>")
print(rag_chain.invoke("<query>"))
print("\n================================================================\n")

template = """Answer the question based only on the following context:
{context}

Question: {question}

Answer in the following language: {language}
"""

prompt = ChatPromptTemplate.from_template(template)

chain = (
    {
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
        "language": itemgetter("language"),
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Replace <question> with your question below:
print(chain.invoke({"question": "<question>", "language": "dutch"}))

print(chain.invoke({"question": "<question>", "language": "dutch"}))





