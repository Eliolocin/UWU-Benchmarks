import configparser
import yaml
import os
import datetime


class Character:
    def __init__(self, name, attributes, smpdialogues, startmessage, rpscene, cotguide):
        self.name = name
        self.attributes = attributes
        self.smpdialogues = smpdialogues
        self.startmessage = startmessage
        self.rpscene = rpscene
        self.cotguide = cotguide

    
class Config:
    def __init__(self, ngram, smp_dialogues_max, test_llm, rp_turns, user_name, gpt_key, gemini_key, claude_key, nai_username, nai_password):
        self.ngram = ngram
        self.smp_dialogues_max = smp_dialogues_max
        self.test_llm = test_llm
        self.rp_turns = rp_turns
        self.user_name = user_name
        self.gpt_key = gpt_key
        self.gemini_key = gemini_key
        self.claude_key = claude_key
        self.nai_username = nai_username
        self.nai_password = nai_password

class Result:
    def __init__(self, characters, config, date_generated, results):
        self.characters = characters
        self.config = config
        self.date_generated = date_generated
        self.results = results

class DataHelper: # Helper class that contains data saving/loading and calculations

    @staticmethod
    def load_character(file_path, config):
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                # print(data)  # Debug: Check the content of data

                # Accessing character data from 'Character' key
                character_data = data['character']
                
                # Access 'sampleDialogues' and 'startingMessage' from the root level, not inside 'Character'
                sample_dialogues = data.get('sampleDialogues', [])
                starting_message = data.get('startingMessage', "")

                # Replace placeholders in the sample dialogues and starting message
                for i in range(len(sample_dialogues)):
                    sample_dialogues[i] = DataHelper.replace_placeholders(sample_dialogues[i], config.user_name, character_data['characterName'])
                starting_message = DataHelper.replace_placeholders(starting_message, config.user_name, character_data['characterName'])

                # Create a Character object (assuming it has attributes: name, attributes, dialogues, and starting_message)
                character = Character(
                    character_data['characterName'],    # Name from 'Character'
                    character_data['attributeList'],    # Attributes from 'Character'
                    sample_dialogues,                   # Dialogues from root level
                    starting_message,                   # Starting message from root level
                    [starting_message],                 # Incomplete roleplay scene starts with the starting_message
                    ""                                  # Empty Chain of Thought guide
                )

                return character
        
    def load_character_directory(directory_path, config):
        characters = []

        # Loop through all files in the directory
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)

            if filename.endswith('.yaml'):
                character = DataHelper.load_character(file_path, config)
                characters.append(character)

        return characters
        
    def load_config(file_path):
        parser = configparser.ConfigParser()
        parser.read(file_path, encoding='utf-8')

        # Extract data from the .ini file with default values
        ngram = parser.getint('Settings', 'ngram', fallback=3) # Default ngram is 3
        smp_dialogues_max = parser.getint('Settings', 'smp_dialogues_max', fallback=3) # Default smp_dialogues_max is 3
        test_llm = parser.get('Settings', 'test_llm', fallback=None)
        rp_turns = parser.getint('Settings', 'rp_turns', fallback=10) # Default rp_turns is 10
        user_name = parser.get('Settings', 'user_name', fallback=None)
        gpt_key = parser.get('APIKeys', 'gpt_key', fallback=None)
        gemini_key = parser.get('APIKeys', 'gemini_key', fallback=None)
        claude_key = parser.get('APIKeys', 'claude_key', fallback=None)
        nai_username = parser.get('NAI', 'nai_username', fallback=None)
        nai_password = parser.get('NAI', 'nai_password', fallback=None)

        # print(nai_username, nai_password, nai_key) # debug
        # Handle empty values if needed
        if not user_name:
            raise ValueError("Username is missing or empty in the configuration file.")
        if not test_llm:
            raise ValueError("LLM not chosen in the configuration file.")
        if not gpt_key:
            raise ValueError("GPT Key is missing or empty in the configuration file. This is needed to run JERA as well as ALMP tests.")
        if test_llm.startswith('gemini') and not gemini_key:
            raise ValueError("Gemini Key is missing or empty in the configuration file.")
        if test_llm.startswith('claude') and not claude_key:
            raise ValueError("Claude Key is missing or empty in the configuration file.")
        if test_llm.startswith('nai') and (not nai_username or not nai_password):
            raise ValueError("NAI credentials are missing or incomplete in the configuration file.")

        config = Config(ngram, smp_dialogues_max, test_llm, rp_turns, user_name, gpt_key, gemini_key, claude_key, nai_username, nai_password)
        # Return the extracted values or use them as needed
        return config
    
    def save_generation(roleplayScene, character, config, prompt):
        # Save the generated roleplay to a .yaml file

        # Split the prompt into lines using \n for better readability
        # Remove empty lines using strip() from consecutive \n\n
        split_prompt = [line for line in prompt.split('\n') if line.strip()]

        generation = {
            'date_generated': datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            'character': {
                'name': character.name,
                'attributes': character.attributes,
                'sampleDialogues': character.smpdialogues,
                'startingMessage': character.startmessage,
                'roleplayScene': roleplayScene,
                'cotGuide': character.cotguide
            },
            'config': {
                'ngram': config.ngram,
                'smp_dialogues_max': config.smp_dialogues_max,
                'test_llm': config.test_llm,
                'rp_turns': config.rp_turns,
                'user_name': config.user_name
            },
            'raw_prompt': split_prompt
        }

        filename = f"generations/{character.name}_{config.test_llm}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.yaml"

        with open(filename, 'w', encoding='utf-8') as file:
            yaml.dump(generation, file, default_flow_style=False)

        print(f"\nGeneration saved successfully as \"{filename}\"")

    # Load a single result file as an object
    @staticmethod
    def load_result(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

            # Parse character data
            characters = []
            for char_data in data['characters_used']:
                char_info = char_data['character']
                name = char_info['name']
                scores = char_info['scores']
                character = Character(name, None, None, None, None, None)
                character.scores = scores
                characters.append(character)

            # Parse config data
            config_data = data['config']
            config = Config(
                config_data['ngram'],
                config_data['smp_dialogues_max'],
                config_data['test_llm'],
                config_data['rp_turns'],
                config_data['user_name'],
                None,
                None,
                None,
                None,
                None
            )

            # Extract date generated and results
            date_generated = data['date_generated']
            results = data['results']

            return Result(characters, config, date_generated, results)

    @staticmethod
    def load_results_directory(directory_path):
        results = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.yaml'):
                file_path = os.path.join(directory_path, filename)
                result = DataHelper.load_result(file_path)
                results.append(result)
        return results
    

    @staticmethod
    def load_generations_directory(directory_path):
        characters = []

        for filename in os.listdir(directory_path):
            if filename.endswith('.yaml'):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    
                    character_data = data['character']
                    name = character_data.get('name', "")
                    attributes = character_data.get('attributes', "")
                    sample_dialogues = character_data.get('sampleDialogues', [])
                    starting_message = character_data.get('startingMessage', "")
                    roleplay_scene = character_data.get('roleplayScene', [])
                    cot_guide = character_data.get('cotGuide', [])

                    character = Character(
                        name,
                        attributes,
                        sample_dialogues,
                        starting_message,
                        roleplay_scene,
                        cot_guide
                    )
                    characters.append(character)

        return characters
    
    def save_results(results):
        # Save the benchmark results to a .yaml file

        filename = f"results/Results_{results['config']['test_llm']}_{results['date_generated']}.yaml"

        with open(filename, 'w', encoding='utf-8') as file:
            yaml.dump(results, file, default_flow_style=False)

        print(f"\nResults saved successfully as \"{filename}\"")

    @staticmethod
    def replace_placeholders(text, user_name, character_name):
        text = text.replace('{{user}}', user_name)
        text = text.replace('{{char}}', character_name)
        return text
    

