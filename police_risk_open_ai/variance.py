# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_variance_analysis.ipynb.

# %% auto 0
__all__ = ['copbot_chat_content', 'copbot_question_intro', 'copbot_question_outro', 'generate_bulk_llm_responses',
           'clean_bulk_llm_return', 'copbot_chat_bulk_assessment']

# %% ../nbs/02_variance_analysis.ipynb 3
import pandas as pd
import os
import re


from .llm import *
from dotenv import load_dotenv
import openai
import time
import statsmodels.api as sm
import statsmodels.formula.api as smf
from tqdm import tqdm
import seaborn as sns



# %% ../nbs/02_variance_analysis.ipynb 6
copbot_chat_content = '''
You are CopBot, an assistant designed to help police officers risk assess missing persons.

Using the information provide on a missing person, you will decide on the appropriate risk grading for the person, from either
- No apparent risk (when there is no apparent risk of harm to either the subject or the public.)
- Low risk (when the risk of harm to the subject or the public is assessed as possible but minimal)
- Medium risk (when the risk of harm to the subject or the public is assessed as likely but not serious.)
- High risk (when the risk of serious harm to the subject or the public is assessed as very likely.)

Risk assessment should be guided by the College of Policing Risk principles.'''



copbot_question_intro = ''' Here are some details of a missing person:

'''

copbot_question_outro = '''

Based on the above, please provide a risk assessment for the missing person, guided by the College of Policing Risk principles, which is either:
- No apparent risk 
- Low risk
- Medium risk
- High risk

Return your answer in the format: 

'Graded as X risk, because of the below risk factors:\n - Y \n - Z \n Given these factors...'

Where X is your risk grading (high, medium, low, or no apparent risk) and Y and Z are a few sentences explaining the most important risks you have identified.

Always return your answer in this format, unless the question can't be answered based on the context, say \"I don't know\"'''



# %% ../nbs/02_variance_analysis.ipynb 8
def generate_bulk_llm_responses(return_count=10,age_list = [5,10,14,16,20,25,50,75,100],ethnicity_list = ['White', 'Mixed', 'Asian', 'Black'], temperature_list = [0,0.5,1,1.5,2]):
    """Generates a bulk set of responses from the LLM model"""

    all_responses = []

    for ethnicity in tqdm(ethnicity_list):
        for age in age_list:
            crime_male_risk_profile = """Jason is a """ + ethnicity + """ male, of around """ + str(age) + """ years old, who has gone missing from his home in London. They are known to have been involved in crime. His disappearance is not out of character."""
            crime_female_risk_profile = """Elisabeth is a """ + ethnicity + """ female, of around """ + str(age) + """ years old, who has gone missing from her home in London. They are known to have been involved in crime. His disappearance is not out of character."""
            out_of_character_male_risk_profile = """Jason is a """ + ethnicity + """ male, of around """ + str(age) + """ years old, who has gone missing from his home in London. They are being reported by family members, who are concerned as this has never happened before"""
            out_of_character_female_risk_profile = """Elisabeth is a """ + ethnicity + """ female, of around """ + str(age) + """ years old, who has gone missing from her home in London. They are being reported by family members, who are concerned as this has never happened before"""
            expected_male_risk_profile = """Jason is a """ + ethnicity + """ male, of around """ + str(age) + """ years old, who has gone missing from his home in London. The informant is not worried, as he says this has happened before and they always come home safe."""
            expected_female_risk_profile = """Elisabeth is a """ + ethnicity + """ female, of around """ + str(age) + """ years old, who has gone missing from her home in London. The informant is not worried, as he says this has happened before and they always come home safe."""

            scenarios = [crime_male_risk_profile, crime_female_risk_profile, out_of_character_male_risk_profile, out_of_character_female_risk_profile,expected_male_risk_profile, expected_female_risk_profile]

            for scenario in scenarios:
                for temperature in temperature_list:
                    individual_circumstances = scenario
                    while True:
                        try:
                            individual_context = create_chat_assistant_content(individual_circumstances, df)
                            question_and_context = copbot_question_intro + individual_circumstances + copbot_question_outro
                            openai_response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            n=return_count,
                            temperature=temperature,
                            messages=[
                                    {"role": "system", "content": copbot_chat_content},
                                    {"role": "user", "content": question_and_context},
                                    {"role": "assistant", "content": individual_context},
                                ]
                            )
                            break  # exit the loop if the API call is successful
                        except Exception as e:
                            print(f"Error: {e}")
                            print("Retrying in 5 seconds...")
                            time.sleep(5)  # wait for 5 seconds before trying again
                    response_df = pd.json_normalize(openai_response['choices']).rename(columns={'message.content':'message'}).drop(columns=['finish_reason', 'index', 'message.role'])
                    response_df['temperature'] = temperature
                    response_df['ethnicity'] = ethnicity
                    response_df['age'] = age
                    response_df['scenario'] = scenario
                    if 'Jason' in scenario:
                        response_df['gender'] = 'male'
                    if 'Elisabeth' in scenario:
                        response_df['gender'] = 'female'
                    if 'been involved in crime' in scenario:
                        response_df['risk'] = 'crime'
                    if 'by family members' in scenario:
                        response_df['risk'] = 'out_of_character'
                    if 'this has happened before' in scenario:
                        response_df['risk'] = 'frequent_missing'
                    print(temperature)
                    print(scenario)
                    all_responses.append(response_df)


    all_response_df = pd.concat(all_responses).rename(columns={'risk':'scenario_risk'})
    
    return all_response_df




# %% ../nbs/02_variance_analysis.ipynb 11
def clean_bulk_llm_return(bulk_return_df):
    """Given a bulk LLM output, cleans it for analysis"""

    bulk_return_df = bulk_return_df.reset_index(drop=True)
    regex_str = 'graded(.*)risk'

    bulk_return_df['message_lower'] = bulk_return_df['message'].str.lower()
    # define the regex pattern
    pattern = r'\b(no apparent|low|medium|high)\s+risk'

    # extract the risk level using regex and store in a new column
    bulk_return_df['risk_grade'] = bulk_return_df['message_lower'].str.extract(pattern, flags=re.IGNORECASE)

    bulk_return_df.loc[bulk_return_df['risk_grade'].isna(),'risk_grade'] = 'missing'

    bulk_return_df.loc[(bulk_return_df['risk_grade'].str.contains('high'))
    ,'risk_eval'] = 'high'
    bulk_return_df.loc[(bulk_return_df['risk_grade'].str.contains('medium'))
    ,'risk_eval'] = 'medium'
    bulk_return_df.loc[(bulk_return_df['risk_grade'].str.contains('low'))
    ,'risk_eval'] = 'low'
    bulk_return_df.loc[(bulk_return_df['risk_grade'].str.contains('no apparent'))
    ,'risk_eval'] = 'absent'

    bulk_return_df.loc[bulk_return_df['risk_eval'].isna(),'risk_eval'] = 'missing'

    bulk_return_df['risk_eval'] = bulk_return_df['risk_eval'].astype('category')

    bulk_return_df['risk_eval'] = pd.Categorical(bulk_return_df['risk_eval'], categories=['missing','absent','low','medium', 'high'],
                        ordered=True)

    risk_score_dict = {'missing':0,'absent':1,'low':2,'medium':3, 'high':4}

    bulk_return_df['risk_score'] = bulk_return_df['risk_eval'].map(risk_score_dict)

    bulk_return_df['risk_score'] =bulk_return_df['risk_score'].astype('int')


    cleaned_response_df =pd.concat([bulk_return_df,pd.get_dummies(bulk_return_df['risk_eval'], prefix='risk_eval')],axis=1) 
    return cleaned_response_df





# %% ../nbs/02_variance_analysis.ipynb 14
def copbot_chat_bulk_assessment(list_of_individual_circumstances, df, return_count=10):
    """Takes a list of individual circumstances and returns a list of responses from the LLM"""

    all_returns_list = []

    scenario_number = 1

    for circumstances in tqdm(list_of_individual_circumstances):
        while True:
            try:
                individual_context = create_chat_assistant_content(circumstances, df)


                question_and_context = copbot_question_intro + circumstances + copbot_question_outro

                openai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                n=return_count,
                messages=[
                        {"role": "system", "content": copbot_chat_content},
                        {"role": "user", "content": question_and_context},
                        {"role": "assistant", "content": individual_context},
                    ]
                )

                response_df = pd.json_normalize(openai_response['choices']).rename(columns={'message.content':'message'}).drop(columns=['finish_reason', 'index', 'message.role'])

                response_df['circumstances'] = circumstances
                response_df['individual_context'] = individual_context
                response_df['scenario_number'] = scenario_number

                all_returns_list.append(response_df)
                scenario_number += 1
                break  # exit the loop if the API call is successful
            except Exception as e:
                print(f"Error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)  # wait for 5 seconds before trying again

    all_returns_df = pd.concat(all_returns_list)

    return all_returns_df
