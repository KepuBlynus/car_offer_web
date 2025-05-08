from flask import Flask, request, render_template, send_file
import os
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
IMAGE_FOLDER = 'static/images'

# Example code-image mapping
code_to_image = {
    "E4S": "e4s.jpg",
    "Z11": "z11.jpg",
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    offer = request.files['offer']
    visualization = request.files['visualization']

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    offer_path = os.path.join(UPLOAD_FOLDER, 'offer.pdf')
    vis_path = os.path.join(UPLOAD_FOLDER, 'visualization.pdf')
    temp_offer = os.path.join(OUTPUT_FOLDER, 'temp_offer.pdf')
    output_path = os.path.join(OUTPUT_FOLDER, 'final_offer.pdf')

    offer.save(offer_path)
    visualization.save(vis_path)

    # Open and process the offer PDF
    doc = fitz.open(offer_path)

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    for code, image_file in code_to_image.items():
                        if code in span["text"]:
                            image_path = os.path.join(IMAGE_FOLDER, image_file)
                            # Get the position of the code
                            x0, y0, x1, y1 = span["bbox"]
                            # Insert image just below the text
                            image_rect = fitz.Rect(x0, y1 + 5, x0 + 300, y1 + 105) # Adjust size/position as needed
                            page.insert_image(image_rect, filename=image_path)

    # Save processed offer to temporary PDF
    doc.save(temp_offer)

    # Merge processed offer and visualization
    merger = PdfMerger()
    merger.append(temp_offer)
    merger.append(vis_path)
    merger.write(output_path)
    merger.close()

    # Prepare the file for download
    response = send_file(output_path, as_attachment=True)

    # Cleanup temp files after response is sent
    @response.call_on_close
    def cleanup():
        try:
            os.remove(offer_path)
            os.remove(vis_path)
            os.remove(temp_offer)
            os.remove(output_path)
        except Exception as e:
            print("Cleanup error:", e)

    return response

import threading

import webview

if __name__ == "__main__":
    import threading

    def run_flask():
        app.run(debug=False, port=5000)

    threading.Thread(target=run_flask).start()
    webview.create_window("Car Offer Tool", "http://127.0.0.1:5000")
    webview.start()