"""
    This script creates video segments based on annotations from a CSV file.
    
    To use you want to go to the bottom of the file and change the `csv_file_path` variable to point to your CSV file.
    You also want your video in the same directory as the video file that the csv file points to.
"""


import os
import csv
import json
import ast
from moviepy.video.io.VideoFileClip import VideoFileClip

def parse_attribute_line(attr_line):
    prefix = "# ATTRIBUTE = "
    attr_json = attr_line[len(prefix):]
    return json.loads(attr_json)

def create_folder_structure(base_output_folder, attributes):
    os.makedirs(base_output_folder, exist_ok=True)
    groups = {"Gestures": {}, "MPs": {}}

    for attr_id, attr in attributes.items():
        aname = attr["aname"]
        cleaned_name = aname.replace(":", "").replace(" ", "_")

        if aname.startswith("G:"):
            category = "Gestures"
        elif aname.startswith("MP:"):
            category = "MPs"
        else:
            continue  # Skip other annotation types

        group_folder = os.path.join(base_output_folder, category)
        os.makedirs(group_folder, exist_ok=True)

        groups[category][attr_id] = {
            "name": cleaned_name,
            "folder": group_folder
        }

    return groups

def extract_segments(csv_path):
    with open(csv_path, 'r') as file:
        lines = file.readlines()

    attr_line = lines[8].strip()
    attributes = parse_attribute_line(attr_line)

    segments = []
    for line in lines[10:]:
        if not line.strip() or line.startswith("#"):
            continue
        row = next(csv.reader([line.strip()]))
        video_file_list = ast.literal_eval(row[1])
        video_file = video_file_list[0]
        start_sec, end_sec = ast.literal_eval(row[3])
        annotations = ast.literal_eval(row[5])
        segments.append({
            'video_file': video_file,
            'start_sec': start_sec,
            'end_sec': end_sec,
            'annotations': annotations
        })

    return attributes, segments

def main(csv_path, base_output_folder="output_segments"):
    attributes, segments = extract_segments(csv_path)
    folders = create_folder_structure(base_output_folder, attributes)

    for i, seg in enumerate(segments):
        video_file = seg['video_file']
        annotations = seg['annotations']

        try:
            full_clip = VideoFileClip(video_file)
            start = seg['start_sec']
            end = seg['end_sec']
            clip = full_clip.subclipped(start, end)
        except Exception as e:
            print(f"Error loading video {video_file}: {e}")
            continue

        gesture_names = []
        mp_verbs = []
        mp_targets = []
        folder_to_use = None

        for attr_id, option_id in annotations.items():
            attr = attributes.get(attr_id)
            if not attr:
                continue

            aname = attr["aname"]
            option_name = attr["options"].get(option_id, f"option_{option_id}")
            formatted_name = f"{aname.replace(':', '').replace(' ', '_')}_{option_name.replace(' ', '_')}"

            if aname.startswith("G:"):
                gesture_names.append(formatted_name)
                folder_to_use = folders["Gestures"][attr_id]["folder"]

            elif aname.startswith("MP:"):
                if "Verb" in aname:
                    mp_verbs.append(option_name.replace(" ", "_"))
                elif "Target" in aname:
                    mp_targets.append(option_name.replace(" ", "_"))
                folder_to_use = folders["MPs"][attr_id]["folder"]

        # Compose output filename
        filename_parts = []
        if gesture_names:
            filename_parts.extend(gesture_names)
        if mp_verbs or mp_targets:
            mp_combo = f"MP_{'-'.join(mp_verbs)}_TO_{'-'.join(mp_targets)}"
            filename_parts.append(mp_combo)

        if not folder_to_use:
            print(f"Skipping segment {i+1}: no valid annotation category found.")
            continue

        filename = f"segment_{i+1}__{'__'.join(filename_parts)}.mp4"
        output_path = os.path.join(folder_to_use, filename)

        try:
            clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                logger=None
            )
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Error writing segment: {e}")

        clip.close()
        full_clip.close()

if __name__ == "__main__":
    csv_file_path = "InguinalH_S210_T1_2024-07-17_002900_003824_annotations.csv"  # Change to the proper CSV file path
    main(csv_file_path)
