# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_llm.ipynb.

# %% auto 0
__all__ = ['copbot_chat_content', 'copbot_question_context', 'query_llm', 'create_context', 'answer_question',
           'answer_sergeant_exam_question', 'conduct_risk_assessment', 'machine_risk_assessment',
           'create_chat_assistant_content', 'create_chat_assistant_question', 'copbot_chat_risk_assessment']

# %% ../nbs/00_llm.ipynb 4
import os
from dotenv import load_dotenv
import pandas as pd
import openai
import tiktoken
from tqdm import tqdm
import numpy as np
from openai.embeddings_utils import distances_from_embeddings


# %% ../nbs/00_llm.ipynb 6
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# %% ../nbs/00_llm.ipynb 7
def query_llm(prompt,model="text-davinci-003"):
    "Given a prompt, will query OpenAI and return the output"
    
    response = openai.Completion.create(model="text-davinci-003", prompt=prompt, temperature=0, max_tokens=7)

    text = response['choices'][0]['text']
    return text


# %% ../nbs/00_llm.ipynb 16
def create_context(
    question, df, max_len=1800, size="ada"
):
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')


    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        
        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4
        
        # If the context is too long, break
        if cur_len > max_len:
            break
        
        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)

# %% ../nbs/00_llm.ipynb 17
def answer_question(
    df,
    model="text-davinci-003",
    question="Am I allowed to publish model outputs to Twitter, without a human review?",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """
    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )
    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the question and context
        response = openai.Completion.create(
            prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""

# %% ../nbs/00_llm.ipynb 21
def answer_sergeant_exam_question(
    df,
    question,
    model="text-davinci-003",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """

    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )

    exam_prompt= f""" Answer the question below, in the format 'The answer is X because Z', where X is the letter of the correct answer (A,B,C or D) and X is the explanation in fewer than 3 sentences. 

    if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:"""

    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the question and context
        response = openai.Completion.create(
            prompt=exam_prompt,
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""

# %% ../nbs/00_llm.ipynb 24
def conduct_risk_assessment(
    df,
    question,
    model="text-davinci-003",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """

    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )

    missing_risk_prompt = f""" Using the information below on a missing person, decide on the appropriate risk grading for the person, from either
- High risk
- Medium risk
- Low risk
- no apparent risk

Return your answer in the format: 'Graded as X risk, because of the below risk factors:
- Y
- Z'

Where X is your risk grading (high, medium, low, or no apparent risk) and Y and Z are a few sentences explaining the most important risks you have identified.

if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:""",

    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the question and context
        response = openai.Completion.create(
            prompt=missing_risk_prompt,
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""

# %% ../nbs/00_llm.ipynb 28
def machine_risk_assessment(
    question,
    df,
    model="text-davinci-003",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """

    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )

    missing_risk_prompt = f""" Using the information below on a missing person, decide on the appropriate risk grading for the person, from either
- High risk
- Medium risk
- Low risk
- no apparent risk

Return your answer in the format: 'Graded as X risk, because of the below risk factors:\n - Y \n - Z \n'

Where X is your risk grading (high, medium, low, or no apparent risk) and Y and Z are a few sentences explaining the most important risks you have identified.

if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:""",

    # If debug, print the raw model response

    
    if debug:
        print("Question:\n" + question)
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the question and context
        response = openai.Completion.create(
            prompt=missing_risk_prompt,
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )

        answer = response["choices"][0]["text"].strip()
        
        return answer, context
    except Exception as e:
        print(e)
        return ""

# %% ../nbs/00_llm.ipynb 32
copbot_chat_content = '''
You are CopBot, an assistant designed to help police officers risk assess missing persons.

Using the information provide on a missing person, you will decide on the appropriate risk grading for the person, from either
- No apparent risk (when there is no apparent risk of harm to either the subject or the public.)
- Low risk (when the risk of harm to the subject or the public is assessed as possible but minimal)
- Medium risk (when the risk of harm to the subject or the public is assessed as likely but not serious.)
- High risk (when the risk of serious harm to the subject or the public is assessed as very likely.)

Risk assessment should be guided by the College of Policing Risk principles.'''



# %% ../nbs/00_llm.ipynb 33
copbot_question_context = '''

Based on the above, please provide a risk assessment for the missing person, guided by the College of Policing Risk principles, which is either:
- No apparent risk 
- Low risk
- Medium risk
- High risk

Return your answer in the format: 

'Graded as X risk, because of the below risk factors:\n - Y \n - Z \n Given these factors...'

Where X is your risk grading (high, medium, low, or no apparent risk) and Y and Z are a few sentences explaining the most important risks you have identified.

Always return your answer in this format, unless the question can't be answered based on the context, say \"I don't know\"'''



# %% ../nbs/00_llm.ipynb 34
def create_chat_assistant_content(
    question, df, max_len=3600, size="ada"
):
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')


    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        
        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4
        
        # If the context is too long, break
        if cur_len > max_len:
            break
        
        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)

# %% ../nbs/00_llm.ipynb 35
def create_chat_assistant_question(missing_person_circumstances):

    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].values, distance_metric='cosine')


    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        
        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4
        
        # If the context is too long, break
        if cur_len > max_len:
            break
        
        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)

# %% ../nbs/00_llm.ipynb 36
def copbot_chat_risk_assessment(individual_circumstances, df, return_context=False, debug_mode=False):
    """Takes a user input string about the individual circumstances of a missing person, and returns a risk assessment"""

    individual_context = create_chat_assistant_content(individual_circumstances, df)

    question_and_context = individual_context + copbot_question_context

    openai_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": copbot_chat_content},
            {"role": "user", "content": individual_circumstances},
            {"role": "assistant", "content": question_and_context},
        ]
    )

    if debug_mode:
        print(openai_response)
        print('\n\n\n')

    if return_context:
        return openai_response['choices'][0]['message']['content'], individual_context
    
    else:
        return openai_response['choices'][0]['message']['content']

    
