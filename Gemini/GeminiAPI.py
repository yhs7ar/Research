import os
import json
import time
import google.generativeai as genai

# Configure the Gemini API with the key from the environment variable
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Error: The GOOGLE_API_KEY environment variable is not set.")
    exit()

# Initialize the Gemini 2.5 Pro model
model = genai.GenerativeModel('gemini-2.5-pro')

def generate_responses(prompts):
    """
    Generates responses from the Gemini model for a list of prompts.

    Args:
        prompts (list): A list of prompt dictionaries.

    Returns:
        list: A list of dictionaries with prompt IDs and their corresponding responses.
    """
    responses = []
    for prompt_data in prompts:
        prompt_id = prompt_data.get("id")
        text_prompt = prompt_data.get("text_prompt")
        video_path = prompt_data.get("video_path")

        print(f"Processing prompt: {prompt_id}")

        try:
            if video_path and os.path.exists(video_path):
                # For multimodal prompts with video
                print(f"Uploading video: {video_path}")
                video_file = genai.upload_file(path=video_path)

                # Wait for the video to be processed
                while video_file.state.name == "PROCESSING":
                    print("Waiting for video to be processed...")
                    time.sleep(10)
                    video_file = genai.get_file(video_file.name)

                if video_file.state.name == "FAILED":
                    raise ValueError(video_file.state.name)

                # Generate content with both text and video
                response = model.generate_content([text_prompt, video_file])

            elif video_path:
                 print(f"Warning: Video path '{video_path}' for prompt '{prompt_id}' does not exist. Treating as a text-only prompt.")
                 response = model.generate_content(text_prompt)
            else:
                # For text-only prompts
                response = model.generate_content(text_prompt)

            responses.append({
                "id": prompt_id,
                "response": response.text
            })
            print(f"Successfully generated response for prompt: {prompt_id}")

        except Exception as e:
            print(f"An error occurred while processing prompt {prompt_id}: {e}")
            responses.append({
                "id": prompt_id,
                "response": f"Error: {e}"
            })

    return responses

if __name__ == "__main__":
    # Define the input and output file paths
    input_json_path = "prompts.json"
    output_json_path = "output.json"

    # Read the prompts from the JSON file
    try:
        # --- THIS IS THE CORRECTED LINE ---
        with open(input_json_path, 'r', encoding='utf-8') as f:
            prompts_to_process = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{input_json_path}' was not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: The file '{input_json_path}' is not a valid JSON file.")
        exit()


    # Generate responses
    generated_responses = generate_responses(prompts_to_process)

    # Write the responses to the output JSON file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(generated_responses, f, indent=4)

    print(f"\nResponses have been written to {output_json_path}")