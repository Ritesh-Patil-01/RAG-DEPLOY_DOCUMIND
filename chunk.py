# import libraries :-
from langchain_text_splitters import RecursiveCharacterTextSplitter

# split the text into chunks :-
def split_text(text,chunk_size=50,chunk_overlap=10) :
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text) 
    return chunks

