from flask import Flask, request, render_template, send_file
import os
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
IMAGE_FOLDER = 'static/images'

code_to_image = {
    "E4S": "e4s.JPEG",
    "A4M": "a4m.JPEG",
    "F49": "f49.JPEG",
    "F84": "f84.JPEG",
    "JB6": "jb6.JPEG",
    "JB7": "jb7.JPEG",
    "LA1": "la1.JPEG",
    "LG7": "lg7.JPEG",
    "P3X": "p3x.JPEG",
    "QA8": "qa8.JPEG",
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    offer = request.files['offer']
    visualization = request.files['visualization']
    insert_images = 'insert_images' in request.form
    insert_banner = 'insert_banner' in request.form

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    offer_path = os.path.join(UPLOAD_FOLDER, 'offer.pdf')
    vis_path = os.path.join(UPLOAD_FOLDER, 'visualization.pdf')

    offer.save(offer_path)
    visualization.save(vis_path)

    doc = fitz.open(offer_path)

    klientas_name = ""
    model_name = "MERCEDES-BENZ SPRINTER SELECT 319CDI TOURER"

    banner_path = os.path.join(IMAGE_FOLDER, "banner.jpg")
    banner_inserted = False

    for page in doc:
        text = page.get_text()
        if "Klientas:" in text and not klientas_name:
            start = text.find("Klientas:") + len("Klientas:")
            klientas_name = text[start:].split("\n")[0].strip()

        if insert_images:
            for code, image_file in code_to_image.items():
                instances = page.search_for(code)
                for inst in instances:
                    image_path = os.path.join(IMAGE_FOLDER, image_file)

                    img_width = 120
                    img_height = 65
                    img_x0 = inst.x1 + 240
                    img_y0 = inst.y0 - 5
                    img_rect = fitz.Rect(img_x0, img_y0, img_x0 + img_width, img_y0 + img_height)

                    page.insert_image(img_rect, filename=image_path, keep_proportion=True, overlay=True)

                    page.draw_rect(img_rect, color=(0, 1, 1), width=1.5, fill_opacity=0.05)
                    shadow_rect = fitz.Rect(img_rect.x0 + 2, img_rect.y0 + 2, img_rect.x1 + 2, img_rect.y1 + 2)
                    page.draw_rect(shadow_rect, color=(0.4, 0.4, 0.4), width=0.5, fill_opacity=0.1)

                    underline_start = fitz.Point(inst.x0, inst.y1 + 1.5)
                    underline_end = fitz.Point(inst.x1 + 5, inst.y1 + 1.5)
                    corner_point = fitz.Point(img_rect.x0 - 10, inst.y1 + 1.5)
                    vertical_to_image = fitz.Point(img_rect.x0 - 10, img_rect.y0 + img_height / 2)

                    page.draw_line(underline_start, underline_end, color=(0, 0.7, 1), width=1.2)
                    page.draw_line(underline_end, corner_point, color=(0, 0.7, 1), width=1.2)
                    page.draw_line(corner_point, vertical_to_image, color=(0, 0.7, 1), width=1.2)
                    page.draw_line(fitz.Point(img_rect.x0, img_rect.y0 + img_height / 2), vertical_to_image, color=(0, 0.7, 1), width=1.2)

        if insert_banner and not banner_inserted:
            label = "Techniniai duomenys:"
            found = page.search_for(label)
            if found:
                for pos in found:
                    banner_rect = fitz.Rect(pos.x0, pos.y0 - 330, pos.x0 + 460, pos.y0 - 210)
                    page.insert_image(banner_rect, filename=banner_path, overlay=True)
                    banner_inserted = True
                    break

    temp_offer_path = os.path.join(OUTPUT_FOLDER, 'temp_offer.pdf')
    doc.save(temp_offer_path)

    vis_reader = PdfReader(vis_path)
    pages = list(vis_reader.pages)

    def is_blank(page):
        return not bool(page.extract_text().strip())

    if len(pages) >= 6:
        pages[0], pages[1], pages[4], pages[5] = pages[4], pages[5], pages[0], pages[1]

    pages = [p for p in pages if not is_blank(p)]
    if pages and is_blank(pages[-1]):
        pages.pop()

    reordered_vis_path = os.path.join(OUTPUT_FOLDER, 'reordered_visualization.pdf')
    with open(reordered_vis_path, 'wb') as f:
        writer = PdfWriter()
        for p in pages:
            writer.add_page(p)
        writer.write(f)

    merger = PdfMerger()
    merger.append(temp_offer_path)
    merger.append(reordered_vis_path)

    final_filename = "Final_offer.pdf"
    final_path = os.path.join(OUTPUT_FOLDER, final_filename)
    merger.write(final_path)
    merger.close()

    return send_file(final_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
