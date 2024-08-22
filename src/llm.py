from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from src.prompts import template,document_template
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM and memory
PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
llm = ChatGroq(
    temperature=0,
    groq_api_key=os.getenv('API'),
    model_name="llama-3.1-8b-instant"
)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=True, prompt=PROMPT)


# loading and splitting file along with embeddings and vector db
def load_and_retrieve(file):
    file = PyPDFLoader(file).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
    chunks = splitter.split_documents(file)
    embeddings = HuggingFaceEmbeddings()
    vectorstore = FAISS.from_documents(documents=chunks,embedding=embeddings)
    return vectorstore.as_retriever()


# RAG chain invoking the load file and retriever and asking the document
def rag_chain(file,question):
    retriever = load_and_retrieve(file)
    prompt = ChatPromptTemplate.from_template(document_template)
    chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
    response = chain.invoke(question)
    return response


#chat handling
def handle_chat(file, question):
    if file:
        return rag_chain(file, question)
    else:
        return conversation.predict(input=question)
