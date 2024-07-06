import json
import os
import sys

def load_metadata(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)

def compare_metadata(master_data, comparison_data):
    differences = []

    for i, (master_ab, comparison_ab) in enumerate(zip(master_data['artboards'], comparison_data['artboards'])):
        if master_ab != comparison_ab:
            differences.append(f"Artboard {i + 1} differences:\nMaster: {master_ab}\nComparison: {comparison_ab}\n")

    for i, (master_tf, comparison_tf) in enumerate(zip(master_data['text_frames'], comparison_data['text_frames'])):
        if master_tf != comparison_tf:
            differences.append(f"Text Frame {i + 1} differences:\nMaster: {master_tf}\nComparison: {comparison_tf}\n")

    for i, (master_obj, comparison_obj) in enumerate(zip(master_data['non_text_objects'], comparison_data['non_text_objects'])):
        if master_obj != comparison_obj:
            differences.append(f"Non-Text Object {i + 1} differences:\nMaster: {master_obj}\nComparison: {comparison_obj}\n")

    return differences

def generate_report(master_file, comparison_file, output_file):
    master_metadata = load_metadata(master_file)
    comparison_metadata = load_metadata(comparison_file)

    with open(output_file, 'w') as report:
        differences = compare_metadata(master_metadata, comparison_metadata)
        if differences:
            report.write(f"Differences between {os.path.basename(master_file)} and {os.path.basename(comparison_file)}:\n")
            for diff in differences:
                report.write(diff + "\n")
            report.write("\n")
        else:
            report.write(f"No differences found between {os.path.basename(master_file)} and {os.path.basename(comparison_file)}.\n\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare-metadata.py <master_metadata.json> <comparison_metadata.json>")
        sys.exit(1)

    master_file_path = sys.argv[1]
    comparison_file_path = sys.argv[2]
    output_file_path = "comparison_report.txt"

    generate_report(master_file_path, comparison_file_path, output_file_path)
    print(f"Comparison report generated: {output_file_path}")
