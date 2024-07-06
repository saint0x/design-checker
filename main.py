import streamlit as st
import subprocess
import os
import shutil
import tempfile
import requests
import threading
from flask import Flask, request, jsonify

# Flask API
app = Flask(__name__)

@app.route('/extract_metadata', methods=['POST'])
def extract_metadata():
    data = request.json
    ai_file_path = data['ai_file_path']
    output_dir = data['output_dir']

    jsx_script = """
    #target illustrator

    function collectAndCategorizeTextLayers(doc) {
        // Create a new layer for the collected text frames
        var collectedTextLayer = doc.layers.add();
        collectedTextLayer.name = "Collected Text";

        var headerSize = 0;
        var subheaderSize = 0;
        var textLayers = [];

        // Function to collect text frames and determine header/subheader sizes
        function collectTextFramesAndSizes(layer) {
            for (var i = layer.textFrames.length - 1; i >= 0; i--) {
                var textFrame = layer.textFrames[i];
                var fontSize = textFrame.textRange.characterAttributes.size;
                textLayers.push({ frame: textFrame, size: fontSize }); // Collect text layer with size
                textFrame.moveToBeginning(collectedTextLayer);

                // Update header and subheader sizes
                if (fontSize > headerSize) {
                    subheaderSize = headerSize;
                    headerSize = fontSize;
                } else if (fontSize > subheaderSize && fontSize < headerSize) {
                    subheaderSize = fontSize;
                }
            }

            for (var j = layer.layers.length - 1; j >= 0; j--) {
                collectTextFramesAndSizes(layer.layers[j]); // Recursion for nested layers
            }
        }

        // Function to categorize and rename text layers
        function categorizeAndRenameTextLayers() {
            var headerCount = 1;
            var subheaderCount = 1;
            var bodyCopyCount = 1;

            for (var i = 0; i < textLayers.length; i++) {
                var layer = textLayers[i];
                var name, count;
                var sizeDifferenceHeader = (layer.size / headerSize) * 100;
                var sizeDifferenceSubheader = (layer.size / subheaderSize) * 100;

                if (sizeDifferenceHeader >= 80) {
                    name = "Header";
                    count = headerCount++;
                } else if (sizeDifferenceSubheader >= 60) {
                    name = "Subheader";
                    count = subheaderCount++;
                } else {
                    name = "Body Copy";
                    count = bodyCopyCount++;
                }

                layer.frame.name = name + " " + count;
            }
        }

        // Iterate through all layers and collect text frames
        for (var i = doc.layers.length - 1; i >= 0; i--) {
            var layer = doc.layers[i];
            if (layer !== collectedTextLayer) { // Avoid recursion on the new layer
                collectTextFramesAndSizes(layer);
            }
        }

        categorizeAndRenameTextLayers();
    }

    // Run the script on the active document
    if (app.documents.length > 0) {
        collectAndCategorizeTextLayers(app.activeDocument);
    } else {
        alert("No document is open");
    }
    """

    try:
        # Save the ExtendScript to a temporary file
        jsx_file_path = os.path.join(output_dir, 'extract-metadata.jsx')
        with open(jsx_file_path, 'w') as jsx_file:
            jsx_file.write(jsx_script)

        # Run the ExtendScript
        command = [
            "osascript", "-e",
            f'do shell script "open -a Adobe\\ Illustrator {ai_file_path}; osascript {jsx_file_path}"'
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Error running metadata extraction script: {result.stderr}")

        return jsonify({"message": "Metadata extraction successful", "output_dir": output_dir})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask():
    app.run(port=5000)

# Start the Flask API concurrently
threading.Thread(target=run_flask).start()

# Streamlit app layout
st.title('Illustrator File Comparison Tool')

st.header("Upload Master AI File")
master_status = st.empty()
master_file = st.file_uploader("Upload Master .ai file", type="ai", key="master")

st.header("Upload Comparison AI File")
comparison_status = st.empty()
comparison_file = st.file_uploader("Upload Comparison .ai file", type="ai", key="comparison")

st.header("Comparison Report")
report_container = st.empty()

if st.button('Compare Metadata'):
    if master_file and comparison_file:
        try:
            # Ensure upload directories exist
            master_dir = os.path.join("uploads", "master")
            compare_dir = os.path.join("uploads", "compare")
            os.makedirs(master_dir, exist_ok=True)
            os.makedirs(compare_dir, exist_ok=True)

            # Save uploaded files to respective directories
            master_path = save_uploaded_file(master_file, master_dir)
            comparison_path = save_uploaded_file(comparison_file, compare_dir)

            # Define the API endpoint
            api_url = "http://127.0.0.1:5000/extract_metadata"

            # Send request to extract metadata for master file
            response_master = requests.post(api_url, json={"ai_file_path": master_path, "output_dir": master_dir})
            if response_master.status_code != 200:
                st.error(f"Error extracting metadata from master file: {response_master.json()['error']}")
            else:
                master_status.success("Metadata extracted from master file.")

            # Send request to extract metadata for comparison file
            response_comparison = requests.post(api_url, json={"ai_file_path": comparison_path, "output_dir": compare_dir})
            if response_comparison.status_code != 200:
                st.error(f"Error extracting metadata from comparison file: {response_comparison.json()['error']}")
            else:
                comparison_status.success("Metadata extracted from comparison file.")

            # Paths to the generated metadata files
            master_metadata_path = os.path.join(master_dir, "master_metadata.json")
            comparison_metadata_path = os.path.join(compare_dir, "comparison_metadata.json")

            # Compare metadata and generate a report
            comparison_script = "compare-metadata.py"
            result = subprocess.run(
                ["python3", comparison_script, master_metadata_path, comparison_metadata_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                report_container.success("Comparison report generated.")
                with open("comparison_report.txt", "r") as report_file:
                    report_content = report_file.read()
                report_container.text_area("Comparison Report", value=report_content, height=400)
                st.download_button('Download Report', report_content.encode('utf-8'), file_name='comparison_report.txt')
            else:
                report_container.error(f"Error generating comparison report: {result.stderr}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        master_status.error("Please upload both a master file and a comparison file.")
