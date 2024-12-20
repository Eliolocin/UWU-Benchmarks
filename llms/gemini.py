import google.generativeai as genai
import sys
import re
sys.path.append('..')
from datahelper import DataHelper

class Gemini:
    @staticmethod
    def generate_roleplay(character, config):
        ##############################
        genai.configure(api_key=config.gemini_key)
        model = genai.GenerativeModel(model_name=config.test_llm)
        safety_settings={
        'HATE': 'BLOCK_NONE',
        'HARASSMENT': 'BLOCK_NONE',
        'SEXUAL' : 'BLOCK_NONE',
        'DANGEROUS' : 'BLOCK_NONE'
        }
        ##############################
        
        roleplayScene = [character.startmessage]  # Initialize roleplayScene with the starting message
        cot_guide = ""  # Initialize Chain of Thought guide for the character
        sample_dialogue = ""  # Initialize dialogue for the character

        # Start preparing the prompt to be sent to the LLM
        prompt = f"Character: {character.name}\nAttributes: {character.attributes}Sample Dialogues:\n"
        for dialogue in character.smpdialogues[:(config.smp_dialogues_max*2)]:
            prompt += f"{dialogue}\n"
            sample_dialogue += f"{dialogue}\n"
            # If config.smp_dialogues_max is 2, then 4 utterances (2 from user character, 2 from test character) will be included in the prompt
        
        # Start Chain of Thought prompting
        # Step 1
        prompt += f"\nStep 1: deeply analyze {character.name}'s personality, motivations, and behavioral traits based on the following attributes and sample dialogues. Reflect on these key questions as you think about how to roleplay the character:" \
              f"\n1. What drives {character.name} emotionally? What are their core desires or fears?" \
              f"\n2. How does {character.name}'s past or experiences shape their current behavior?" \
              f"\n3. How does {character.name} typically speak and interact with others based on their attributes?" \
              f"\n4. In what situations does {character.name} show vulnerability, strength, or hesitation?\n\n"
        
        ##############################
        cot_response = model.generate_content(contents=prompt, safety_settings=safety_settings)
        ##############################

        cot_generation = cot_response.text
        character.cotguide += f"{cot_generation}\n"

        prompt += f"{cot_generation}\n"
        # Step 2
        prompt += f"\nStep 2: Now, based on {character.name}'s analysis in Step 1, outline a behavioral strategy for roleplaying {character.name}. Consider the following:" \
              f"\n1. What communication style or tone should {character.name} use in typical conversations (e.g., formal, hesitant, kind, direct)?" \
              f"\n2. How should {character.name} in common situations (e.g., conflict, praise, meeting strangers)?" \
              f"\n3. Which specific traits or speech patterns must be consistently present to remain true to {character.name}'s core personality?" \
              f"\n4. What should {character.name} avoid doing or saying to remain authentic to their defined attributes?\n\n"
        
        ##############################
        cot_response = model.generate_content(contents=prompt, safety_settings=safety_settings)
        ##############################

        cot_generation = cot_response.text
        character.cotguide += f"{cot_generation}\n"
        prompt += f"{cot_generation}\n"
        # Step 3
        prompt += f"\nStep 3: Now, the following is a new roleplay scenario. Only generate one response a time from the current speaker. The characters MUST alternately speak ({character.name} THEN {config.user_name},vice-versa). Try to keep the roleplay scene playing for as long as possible between {config.user_name} and {character.name} as well as follow the outline you made in Steps 1 and 2 as a guide. Don't forget {character.name}'s attributes and way of speech, as seen in:\n\nAttributes: {character.attributes}Sample Dialogues:\n{sample_dialogue}\nMake sure to keep the dialogue dynamic and not too formulaic, following the sample dialogues and demonstrated speech style, especially for characters with certain habits (such as stuttering, replying in all caps, or using exclamations '!' or tildes '~', ONLY if present) but avoid the sentence structure itself from being repetitive (always starting with '{character.name} does X' into '{character.name} says X' pattern is bad and formulaic. Instead, use a mix of actions preceding speech, speech preceding actions, subtle actions within spoken lines, and variations in sentence starters (not only one of these, use all of them as demonstrated in the sample dialogues), as well as proper usage of pronouns and character's name. Continue the next empty line. \n\n{character.startmessage}"

        # Start roleplay scene generation with LLM
        conversation_turns = 1  # Start counting after the initial message
        current_speaker = config.user_name  # Alternate turns starting with the 'User'
        print(prompt+"\n"+current_speaker+": ")  # Debug: Print the prompt
        help_prompt = ""  # Additional Prompt to guide LLM
        contents = ""
        while conversation_turns < config.rp_turns*2:
            response = None
            retries = 5 # Number of retries in case of failure
            while retries > 0:
                if current_speaker == character.name:
                    help_prompt = f"\nThe current speaker is {character.name}. Continue the dialogue as {character.name} only, do NOT roleplay as {config.user_name}. Do NOT speak or ACT on the behalf of {config.user_name} in your own line. As {character.name}, use your outline for roleplaying {character.name}, as well as {character.name}'s given Attribute List and Sample Dialogues as reference to learn how they should act or speak.\n"
                else:
                    help_prompt = f"\nThe current speaker is {config.user_name}. Continue the dialogue as {config.user_name} only, do NOT roleplay as {character.name}. Do NOT speak or ACT on the behalf of {character.name} in your own line. As {config.user_name}, try to challenge {character.name}'s roleplaying ability by doing actions or asking questions that would bring out {character.name}'s character traits or personality.\n"

                tempprompt = prompt+"\n"+current_speaker+": "  # Add the current speaker to the prompt
                if retries < 5:
                    tempprompt += f"\n[Note: Ensure the response starts with {current_speaker}: and adheres to the alternating dialogue rule. Do NOT include lines for other speakers.]"

                contents = help_prompt+tempprompt+tempprompt
                ##############################
                cot_response = model.generate_content(contents=contents, safety_settings=safety_settings)
                ##############################

                # print("Unclean text: "+current_speaker+": "+response.choices[0].content)
                generated_text = Gemini.trim_response(current_speaker+": "+response.text)
                # print(generated_text)  # Debug: Print the generated text


                # Ensure proper formatting
                if Gemini.is_valid_response(current_speaker, generated_text):
                    break  # Valid response found, exit retry loop
                else:
                    retries -= 1
                    # tempprompt += f"\n[Note: Ensure the response starts with {current_speaker}: and adheres to the alternating dialogue rule. Do NOT include lines for other speakers.]"
                    # print(f"(Invalid response, retrying... {retries} retries left.)")

            if retries == 0:
                raise Exception("Failed to generate valid response after multiple attempts, please lower number of turns or avoid inappropriate scenarios.")

            # Append the generated text to roleplayScene and prompt
            print(generated_text)  # Debug: Print the generated text
            roleplayScene.append(generated_text)
            prompt += generated_text
            #print(generated_text)  # Debug: Print the generated text

            # Switch the speaker
            current_speaker = character.name if current_speaker == config.user_name else config.user_name
            conversation_turns += 1

        # Save result as a text file
        DataHelper.save_generation(roleplayScene, character, config, prompt)
        return roleplayScene

# Updated validation to check for multiple lines and correct speaker format
    @staticmethod
    def is_valid_response(current_speaker, generated_text):
        
        if not generated_text.startswith(current_speaker+":"):
            return False
        
        # If there are two or more colons, return false
        if generated_text.count(":") > 1:
            return False
        
        return True

    @staticmethod
    def trim_response(text):
        # Match the first speaker-dialogue pair
        pattern = re.compile(r"([^:]+):\s*(.+?)(?=(?:^[^:]+:|$))", re.DOTALL | re.MULTILINE)
        matches = pattern.findall(text)
        
        if matches:
            # Get the first match: speaker and dialogue
            speaker = matches[0][0].strip()
            dialogue = matches[0][1].strip()
            
            # Remove redundant speaker prefixes in the dialogue
            if dialogue.startswith(f"{speaker}:"):
                dialogue = dialogue[len(f"{speaker}:"):].strip()
            
            # Ensure dialogue is cleaned of excess newlines and spaces
            dialogue = re.sub(r'\s+', ' ', dialogue)
            
            return f"{speaker}: {dialogue}"
        
        return text  # Return the original text if no matches are found