import asyncio
import sys
import re
sys.path.append('..')
from datahelper import DataHelper

from novelai_api import NovelAIAPI
from novelai_api.Preset import PREAMBLE, Model, Preset
from novelai_api.GlobalSettings import GlobalSettings
from novelai_api.Tokenizer import Tokenizer
from novelai_api.utils import b64_to_tokens

class NovelAI:
    @staticmethod
    async def generate_roleplay(character, config):
        # Set up NovelAI API
        api = NovelAIAPI()
        await api.high_level.login(config.nai_username, config.nai_password)
        
        # Convert config.test_llm to the appropriate Model enum
        model_name = config.test_llm.split('-')[1].capitalize()
        
        # Select model (you can choose based on your config)
        model = getattr(Model, model_name)  # Dynamically select model based on config.test_llm
        
        # Set up preset and global settings
        preset = Preset.from_default(model)
        print(preset)
        tokenizer_name = Tokenizer.get_tokenizer_name(model)
        print(f"Tokenizer selected: {tokenizer_name}")
        preset.min_length = 50   # Adjust as needed
        preset.max_length = 150  # Adjust as needed
        # preset.temperature = 0.7  # Adjust as needed
        global_settings = GlobalSettings()
        
        # Define stop sequences
        stop_sequences = [f"\n{character.name}:", f"\n{config.user_name}:", f"{character.name}:", f"{config.user_name}:"]
        # Encode stop sequences into tokens
        stop_sequences_tokens = [Tokenizer.encode(model, seq) for seq in stop_sequences]
        
        roleplayScene = [character.startmessage]  # Initialize roleplayScene with the starting message
        sample_dialogue = ""  # Initialize dialogue for the character

        # Include the PREAMBLE
        preamble = PREAMBLE[model]
        
        # Start preparing the prompt to be sent to the LLM
        prompt_text = f"{character.attributes}\n"
        for dialogue in character.smpdialogues[:(config.smp_dialogues_max*2)]:
            prompt_text += f"{dialogue}\n"
            sample_dialogue += f"{dialogue}\n"
            # If config.smp_dialogues_max is 2, then 4 utterances (2 from user character, 2 from test character) will be included in the prompt
        # Add the separator and note
        prompt_text += "[The following is a new roleplay scene.]\n"
        # prompt_text += f"[Note: The following is a new roleplay, make sure to adhere to the alternating dialogue rule. Do NOT include lines for other speakers and act {character.name} as best you can based on her sample dialogues and attributes given.]\n"
        prompt_text += character.startmessage  # Add the starting message to the prompt

        # Combine the preamble and the prompt_text
        full_prompt = preamble + "\n" + prompt_text

        # Encode the full prompt into tokens
        prompt_tokens = Tokenizer.encode(model, full_prompt)
        
        print(full_prompt)  # Debug: Print the full prompt
        help_prompt = ""  # Additional Prompt to guide LLM
        contents = ""
        conversation_turns = 1  # Start counting after the initial message
        current_speaker = config.user_name  # Alternate turns starting with the 'User'
        
        while conversation_turns < config.rp_turns*2:
            retries = 5  # Number of retries in case of failure
            while retries > 0:
                # Generate content with stop sequences
                gen = await api.high_level.generate(prompt_tokens, model, preset, global_settings, stop_sequences=stop_sequences_tokens)
                output_tokens = b64_to_tokens(gen["output"])
                generated_text = Tokenizer.decode(model, output_tokens)

                other_speaker = character.name if current_speaker == config.user_name else config.user_name

                # Trim and validate the response
                generated_text = NovelAI.trim_response(generated_text, current_speaker, other_speaker)

                # Ensure proper formatting
                if NovelAI.is_valid_response(current_speaker, generated_text):
                    break  # Valid response found, exit retry loop
                else:
                    retries -= 1
                    print(f"(Invalid response, retrying... {retries} retries left.)")
                    print(f"Generated text: {generated_text}")

            if retries == 0:
                raise Exception("Failed to generate valid response after multiple attempts, please lower the number of turns or avoid inappropriate scenarios.")

            # Append the generated text to roleplayScene and prompt_tokens
            print(generated_text)  # Debug: Print the generated text
            roleplayScene.append(generated_text)
            # Append the generated text to prompt_tokens
            generated_tokens = Tokenizer.encode(model, generated_text)
            prompt_tokens += generated_tokens

            # Switch the speaker
            current_speaker = character.name if current_speaker == config.user_name else config.user_name
            conversation_turns += 1

        # Save result as a text file
        DataHelper.save_generation(roleplayScene, character, config, full_prompt)
        return roleplayScene

    @staticmethod
    def is_valid_response(current_speaker, generated_text):
        if not generated_text.startswith(current_speaker + ":"):
            return False

        # If there are two or more colons, return false
        if generated_text.count(":") > 1:
            return False

        return True

    @staticmethod
    def trim_response(text, current_speaker, other_speaker):
        # Ensure text is a string
        text = str(text)
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # If '***' is in text, cut text at that point (inclusive)
        if '***' in text:
            text = text.split('***')[0].strip()
        
        # Normalize spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Find the position where the current speaker's dialogue starts
        start_index = text.find(f"{current_speaker}:")
        if start_index == -1:
            # If current speaker not found, return empty string
            return ''
        
        # Move past the speaker's name and colon to get to the dialogue
        dialogue_start = start_index + len(f"{current_speaker}:")
        dialogue = text[dialogue_start:].strip()
        
        # If there's no dialogue after the colon, return empty string
        if not dialogue:
            return ''
        
        # Build a regex pattern to find the next speaker's name followed by a colon
        pattern = re.compile(rf'\b({re.escape(current_speaker)}|{re.escape(other_speaker)}):', re.IGNORECASE)
        # Search for the next speaker's name starting after the current speaker's dialogue begins
        match = pattern.search(text, pos=dialogue_start)
        if match:
            end_index = match.start()
            dialogue = text[start_index:end_index].strip()
        else:
            dialogue = text[start_index:].strip()
        
        # Trim incomplete sentences at the end
        # Find the last occurrence of '.', '!', '?', or '"'
        last_punct_match = re.search(r'[.!?"](?=[^.!?"]*$)', dialogue)
        if last_punct_match:
            end_pos = last_punct_match.end()
            dialogue = dialogue[:end_pos]
        else:
            # If no sentence-ending punctuation found, keep the dialogue as-is
            pass  # No action needed; retain the entire dialogue
        
        # After trimming, check again if there's any dialogue
        dialogue_content = dialogue[len(f"{current_speaker}:"):].strip()
        if not dialogue_content:
            return ''
        
        return dialogue




