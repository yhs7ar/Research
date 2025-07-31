import os
import json

def generate_prompts(base_dir, output_file, id_tag="Benchmarking", text_prompt="What is the motion primitive that is happening in this video? Think through it step by step and provide an action triplet for each hand in the video."):
    prompts = []

    # Walk through the directory structure
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(('.mp4')):  # Extendable
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=os.getcwd())  # Make it relative to current working directory

                prompt = {
                    "id": id_tag,
                    "text_prompt": text_prompt,
                    "video_path": relative_path.replace("\\", "/")  # Normalize for JSON
                }

                prompts.append(prompt)

    # Write to JSON
    with open(output_file, 'w') as f:
        json.dump(prompts, f, indent=4)

    print(f"Generated {len(prompts)} prompts in '{output_file}'.")

# Example usage
if __name__ == "__main__":
    directory_to_scan = "K:/Research/Benchmark_1.0/MPs"  # Change this path as needed
    output_json_file = "multimodal_prompts_2.json"
    generate_prompts(directory_to_scan, output_json_file)
