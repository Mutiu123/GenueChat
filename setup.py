from setuptools import find_packages, setup

setup(
    name="GenueChat",
    version="1.0.0",
    author="Mutiu Adegboye",
    author_email="adegboyemutiu@gmail.com",
    description="Enterprise RAG chatbot with FastAPI, JWT auth, and Prometheus monitoring",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.111.0",
        "uvicorn[standard]>=0.29.0",
        "pydantic>=2.7.0",
        "pydantic-settings>=2.2.0",
        "langchain>=0.2.0",
        "langchain_community>=0.2.0",
        "langchain_huggingface>=0.0.3",
        "langchain_groq>=0.1.0",
        "pypdf>=4.0.0",
        "faiss-cpu>=1.8.0",
        "motor>=3.4.0",
        "PyJWT>=2.8.0",
        "python-dotenv>=1.0.0",
        "prometheus-client>=0.20.0",
    ],
)
