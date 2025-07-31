import os
import json

def generate_prompts(source_dir, output_file, static_base="/scratch/yhs7ar/VideoLLaMA3 Work/Benchmark_1.0/MPs"):
    prompts = []

    # Traverse all files in source_dir
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.mp4')):
                rel_path = os.path.relpath(os.path.join(root, file), start=source_dir)
                # Normalize and construct the video path using static base
                video_path = os.path.join(static_base, rel_path).replace("\\", "/")

                prompt = {
                    "text": "Based on the descriptions I have told you, what is the gesture that is happening in this video? Think through it step by step.",
                    "video": video_path
                }

                prompts.append(prompt)

    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(prompts, f, indent=4)

    print(f"Generated {len(prompts)} prompts in '{output_file}'.")

# Example usage
if __name__ == "__main__":
    directory_to_scan = "K:/Research/Benchmark_1.0/MPs"  # This is your local path to scan
    output_json_file = "multimodal_prompts_G.json"
    generate_prompts(directory_to_scan, output_json_file)
