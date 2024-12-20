from openai import OpenAI
import ast
import re

class JERA:
    def __init__(self):
        # Initialize the questions dictionary as a class attribute
        self.questions = {}

    # Function to generate the questionnaire prompt
    def generate_questionnaire(self, charName, charDesc, charSmpDialogue, rpScene):
        # Likert scale questions, 3 categories with 10 questions each
        # Each question is a tuple: (question_text, is_negative)

        self.questions = {
            "Immersivity": [
                (f"Did the LLM's portrayal of {charName} greatly enhance your enjoyment of the roleplay?", False),
                (f"Did you feel a strong connection to the story through the LLM's portrayal of {charName}?", False),
                (f"Was interacting with the LLM portraying {charName} extremely enjoyable?", False),
                (f"Did you feel fully immersed in the roleplay with the LLM as {charName}?", False),
                (f"Did the roleplay feel highly emotionally compelling due to the LLM's portrayal of {charName}?", False),
                (f"Did the LLM's responses as {charName} feel completely natural and appropriate?", False),
                (f"Was {charName}'s role exceptionally convincing during the interaction?", False),
                (f"Did the LLM make the roleplay significantly less engaging and fun as {charName}?", True),
                (f"Did the LLM's portrayal of {charName} detract noticeably from your enjoyment of the roleplay?", True),
                (f"Did the LLM fail to create an immersive experience as {charName}?", True),
            ],
            "Consistency": [
                (f"Did the LLM consistently maintain {charName}'s mannerisms and speech style without deviation?", False),
                (f"Did the LLM stay in character as {charName} at all times?", False),
                (f"Did the LLM demonstrate a thorough understanding of {charName}'s emotional state?", False),
                (f"Was the LLM's behavior entirely consistent with {charName}'s character description?", False),
                (f"Did the LLM frequently break character as {charName}?", True),
                (f"Was the LLM's portrayal of {charName} inconsistent or contradictory?", True),
                (f"Did the LLM's actions accurately reflect {charName}'s goals and motivations?", False),
                (f"Did the LLM perform actions unfitting or inappropriate for {charName}'s personality?", True),
                (f"Did the LLM react inappropriately to your actions as {charName}?", True),
                (f"Did the LLM maintain the continuity of {charName}'s personality throughout the roleplay?", False),
            ],
            "Creativity": [
                (f"Did the LLM avoid repetition and redundancy as {charName}?", False),
                (f"Did the LLM integrate new information seamlessly into the roleplay?", False),
                (f"Did the LLM create unique and dynamic responses as {charName}?", False),
                (f"Did the LLM respond innovatively to changes in the roleplay?", False),
                (f"Did the LLM show exceptional originality in portraying {charName}?", False),
                (f"Did the LLM fail to bring creativity to the roleplay as {charName}?", True),
                (f"Did the LLM's portrayal of {charName} feel predictable or uninspired?", True),
                (f"Did the LLM introduce new ideas or twists that enriched the roleplay?", False),
                (f"Did the LLM's actions spark new and engaging developments?", False),
                (f"Did the LLM lack spontaneity during the roleplay as {charName}?", True),
            ]
        }

        # Prompt for the Judge LLM
        prompt = f"""You are an evaluator of an LLM's performance as a roleplayer. Your task is to critically assess the LLM's portrayal of {charName} based on the provided character description and sample dialogues. Be strict and objective in your evaluation. High scores should be reserved for exceptional performance.

{charName}'s Character Description:
{charDesc}

{charName}'s Character Sample Dialogues:
{charSmpDialogue}

Roleplay Scene:
{rpScene}

Please answer the following 30 questions using a 10-point Likert scale:

1: Not at all
2: Very little
3: Slightly
4: Somewhat
5: Moderately
6: Fairly
7: Quite a bit
8: Very much
9: Extremely
10: Absolutely

Use the full range of the scale and avoid being overly lenient. For negatively worded questions (marked with an asterisk *), lower scores indicate better performance, and you should reverse the scoring when calculating the total score.

**Calibration Guidelines:**

- **Scores 1-3**: The LLM did not meet the criterion or performed poorly.
- **Scores 4-6**: The LLM met the criterion to an acceptable or average extent.
- **Scores 7-8**: The LLM performed well and met the criterion above average.
- **Scores 9-10**: The LLM exceeded expectations and demonstrated exceptional performance.

Provide your scores as a list of 30 integers like [7, 5, 6, ..., 3], where each score corresponds to the question in order.

Your response should ONLY be the array of 30 integers, and nothing else.
"""

        idx = 1
        for category, qs in self.questions.items():
            prompt += f"\n{category}:\n"
            for q_text, is_negative in qs:
                if is_negative:
                    prompt += f"* {idx}. {q_text} (Negative)\n"
                else:
                    prompt += f"- {idx}. {q_text}\n"
                idx += 1

        return prompt

    # Function to call GPT API and get the evaluation
    def calculate_jera(self, character_name, character_description, character_smpdialogue, roleplay_scene, config):
        max_retries = 3
        for attempt in range(max_retries):
            jera_prompt = self.generate_questionnaire(character_name, character_description, character_smpdialogue, roleplay_scene)
            
            # Call GPT-4 API
            client = OpenAI(api_key=config.gpt_key)

            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strict and objective roleplay evaluator. Provide ONLY the array of scores as your response."},
                    {"role": "user", "content": jera_prompt}
                ],
                model="gpt-4",
            )

            # Extract the array of scores from the response
            response_text = response.choices[0].message.content.strip()

            # Extract all numbers between 1 and 10 from the response
            jera_array = [int(num) for num in re.findall(r'\b(10|[1-9])\b', response_text)]

            expected_num_questions = sum(len(qs) for qs in self.questions.values())

            if len(jera_array) != expected_num_questions:
                print(f"Attempt {attempt+1}: Expected {expected_num_questions} scores, but got {len(jera_array)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    continue
                else:
                    print("Maximum retries reached. Returning None.")
                    return None
            else:
                print("Scores:", jera_array)
                break  # Exit the retry loop if we have the correct number of scores

        # Define the negative questions indices
        negative_indices = []
        idx = 0
        for category, qs in self.questions.items():
            for q_text, is_negative in qs:
                if is_negative:
                    negative_indices.append(idx)
                idx += 1

        # Reverse the scores for negative questions
        # For negative questions, reverse the scoring: score = 11 - original_score
        for idx in negative_indices:
            original_score = jera_array[idx]
            reversed_score = 11 - original_score
            jera_array[idx] = reversed_score

        # Now compute the scores
        imm_score = sum(jera_array[:10])
        con_score = sum(jera_array[10:20])
        cre_score = sum(jera_array[20:30])

        print("Immersion Score: ", imm_score)
        print("Consistency Score: ", con_score)
        print("Creativity Score: ", cre_score)

        jera_score = imm_score + con_score + cre_score

        return jera_score
