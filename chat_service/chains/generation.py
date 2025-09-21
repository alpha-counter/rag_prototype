from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


llm = ChatOpenAI(temperature=0)

system = """You are an assistant for question-answering tasks. If you don't know the answer, just say that you don't know. \n
Answer the user question and provide citations. If none of the articles answer the question, just say you don't know. \n

Remember, you must return both an answer and citations. A citation consists of a VERBATIM quote that \n
justifies the answer and the Source with Page numbers from the metadata of the quoted article. Return a citation for every quote across all articles \n
that justify the answer. Use the following format for your final output:

<cited_answer>
    <answer></answer>
    <citations>
        <citation><source></source><page></page><quote></quote></citation>
        <citation><source></source><page></page><quote></quote></citation>
        ...
    </citations>
</cited_answer>
"""

human = """Use the following pieces of retrieved context to answer the question. \n
Question: {question} 
Context: {context} 
Answer:
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", human),
    ]
)

# prompt = hub.pull("rlm/rag-prompt")

generation_chain = prompt | llm | StrOutputParser()