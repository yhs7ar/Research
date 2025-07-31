import json
import torch
import os
from transformers import AutoModelForCausalLM, AutoProcessor
from torch import amp

# Paths
model_cache_dir = "/sfs/weka/scratch/yhs7ar/huggingface"
json_input_path = "prompts.json"
model_name = "DAMO-NLP-SG/VideoLLaMA3-2B"

# Load model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    cache_dir=model_cache_dir,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# Load processor
processor = AutoProcessor.from_pretrained(
    model_name,
    cache_dir=model_cache_dir,
    trust_remote_code=True,
)

# Load prompts
with open(json_input_path, "r") as f:
    data = json.load(f)

# Inference loop
for entry in data:
    video_path = entry.get("video", "")
    question = entry.get("text", "").strip()

    if video_path and not os.path.exists(video_path):
        print(f"[Warning] Skipping missing video: {video_path}")
        continue

    # Build conversation
    content = [{"type": "text", "text": question}]
    if video_path:
        content.insert(0, {
            "type": "video",
            "video": {"video_path": video_path, "fps": 3, "max_frames": 128}
        })

    conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": content},
    ]

    try:
        # Preprocess
        inputs = processor(conversation=conversation, return_tensors="pt", truncation=True)

        # Ensure proper types and dimensions
        for key, val in inputs.items():
            if isinstance(val, torch.Tensor):
                inputs[key] = val.to(model.device)

        if "pixel_values" in inputs:
            # Reshape pixel values if needed (model-specific)
            if len(inputs["pixel_values"].shape) == 2:
                print(f"[Fix] Reshaping pixel_values: {inputs['pixel_values'].shape}")
                try:
                    num_frames = 128
                    inputs["pixel_values"] = inputs["pixel_values"].reshape(-1, 3, 14, 14)
                except Exception as e:
                    print(f"[ERROR] Bad pixel_values shape: {e}")
                    continue
            inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

        # Print tensor shapes for debug
        print(f"[INFO] Processing: {video_path if video_path else '[text only]'}")
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor):
                print(f"  - {k}: {v.shape}")

        # Generate output
        with torch.no_grad(), amp.autocast("cuda", dtype=torch.bfloat16):
            output_ids = model.generate(**inputs, max_new_tokens=128, max_length=16384)

        response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
        print(f"\n--- Response for {video_path if video_path else '[text only]'} ---\n{response}")

    except Exception as e:
        print(f"[ERROR] Failed to process {video_path if video_path else '[text only]'}: {e}")
        continue

    torch.cuda.empty_cache()
