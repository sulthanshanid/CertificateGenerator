from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import json
import os
from datetime import datetime
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['OUTPUT_FOLDER'] = 'static/output/'
app.config['FONT_FOLDER'] = 'static/fonts/'

# Load or create config.json
if not os.path.exists('config.json'):
    with open('config.json', 'w') as f:
        json.dump({}, f)

# Load configuration data
def load_config():
    with open('config.json') as f:
        return json.load(f)

# Save configuration data
def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

# Load log data
def load_log_data():
    if not os.path.exists('logs.json'):
        return []
    with open('logs.json') as f:
        return json.load(f)

# Save log data
def save_log_data(log_data):
    with open('logs.json', 'w') as f:
        json.dump(log_data, f, indent=4)

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', templates=config)

@app.route('/admin')
def admin_panel():
    config = load_config()
    log_data = load_log_data()
    return render_template('admin.html', templates=config, logs=log_data, yconfig=config)

from PIL import Image, ImageDraw, ImageFont
import os
import zipfile
from datetime import datetime
from flask import request, send_file

from PIL import Image, ImageDraw, ImageFont
import os
import zipfile
from datetime import datetime
from flask import request, send_file

def apply_capitalization(name, capitalization_style):
    if capitalization_style == '1':
        return name.lower()  # Full small
    elif capitalization_style == '2':
        return name.title()  # Word Capitalized
    elif capitalization_style == '3':
        return name.upper()  # Full Capitalized
    return name  # Do nothing

@app.route('/generate', methods=['POST'])
def generate_certificate():
    name = request.form['name']
    year = request.form['year']
    selected_templates = request.form.getlist('template')  # For multiple selections

    config = load_config()
    year_category = f"{year}_year"
    output_files = []

    # Load the existing log data
    log_data = load_log_data()

    # Process each selected template
    for template_name in selected_templates:
        template_config = config.get(year_category, {}).get(template_name)

        if not template_config:
            return "Invalid Template"

        # Get the capitalization style from the template config
        capitalization_style = template_config.get('capitalization', '4')  # Default to 'Do Nothing'

        # Apply the capitalization style to the name
        formatted_name = apply_capitalization(name, capitalization_style)

        # Log the certificate generation
        log_data.append({
            "name": formatted_name,
            "template": template_name,
            "year": year_category,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Process each template and save the certificate
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{template_name}.png")
        font_path = os.path.join(app.config['FONT_FOLDER'], template_config['font'])
        font_size = template_config['font_size']
        position = tuple(template_config['position'])
        font_color = template_config.get('font_color', 'black')
        align_value = template_config.get('align', 1)  # Default to 1 (auto-align)

        template = Image.open(template_path)
        draw = ImageDraw.Draw(template)
        font = ImageFont.truetype(font_path, font_size)

        # Get the size of the name text
        text_width, text_height = draw.textsize(formatted_name, font=font)

        # Check alignment logic
        if align_value == 1:
            print("1",template_name)
            # Auto align: Center the text horizontally and use y coordinate from config
            x = (template.width - text_width) // 2  # Center the text
            y = position[1]  # Use the y-coordinate from template config
        elif align_value == 2:
            print("2",template_name)
            # Do not align: Use the x and y coordinates directly from template config
            x, y = position

        # Draw the name on the template
        draw.text((x, y), formatted_name, font=font, fill=font_color)

        # Save the generated certificate
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{formatted_name}_{template_name}_certificate.png")
        template.save(output_path)
        output_files.append(output_path)

    # Save the updated log data
    save_log_data(log_data)

    # Create a ZIP file of all generated certificates
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{formatted_name}_certificates.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in output_files:
            zipf.write(file, os.path.basename(file))

    # Return the ZIP file to the user
    return send_file(zip_path, as_attachment=True)


# Function to load log data (from a file or a database)
def load_log_data():
    log_file = "certificate_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return json.load(f)
    else:
        return []

# Function to save the log data (to a file or a database)
def save_log_data(log_data):
    log_file = "certificate_log.json"
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=4)

@app.route('/upload', methods=['POST'])
def upload_template():
    template_file = request.files['template']
    template_name = request.form['template_name']
    font_file = request.files['font']
    font_size = int(request.form['font_size'])
    year = request.form['category'] 
    points = request.form['points']
    capitalization = request.form['capitalization']
    align = request.form['align']   # New field for year/category

    # Save template image
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{template_name}.png")
    template_file.save(template_path)

    # Save font file
    font_path = os.path.join(app.config['FONT_FOLDER'], font_file.filename)
    font_file.save(font_path)

    # Save template configuration with font path under the correct year category
    config = load_config()
    year_category = f"{year}"

    if year_category not in config:
        config[year_category] = {}

    config[year_category][template_name] = {
        "font": font_file.filename,
        "font_size": font_size,
        "position": [0, 0],
        "font_path": font_path,
        "font_color": "#000000",  # Default color (black)
        "points": points,
        "capitalization":capitalization,
        "align":align
    }
    save_config(config)
    
    return redirect(url_for('set_position', template_name=template_name, year_category=year, font_file=font_path))

@app.route('/set-position/<year_category>/<template_name>', methods=['GET', 'POST'])
def set_position(year_category, template_name):
    # Retrieve the font file path from config
    config = load_config()
    template_config = config.get(year_category, {}).get(template_name)

    if not template_config:
        return "Font not found for this template", 400

    # Pass the font path and category info to the template
    return render_template('position.html', template_name=template_name, year_category=year_category, font_file=template_config['font'])


@app.route('/save-position', methods=['POST'])
def save_position():
    template_name = request.form['template_name']
    year_category = request.form['year']
    x = int(request.form['x'])
    y = int(request.form['y'])
    font_size = int(request.form['font_size'])
    font_color = request.form['font_color']

    config = load_config()
    if year_category in config and template_name in config[year_category]:
        config[year_category][template_name]['position'] = [x, y]
        config[year_category][template_name]['font_size'] = font_size
        config[year_category][template_name]['font_color'] = font_color
        save_config(config)
    
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})

@app.route('/get-templates/<year>', methods=['GET'])
def get_templates_for_year(year):
    # Load configuration
    config = load_config()
    
    # Create the year category string
    year_category = f"{year}_year"
    
    # Check if the year exists in the config
    if year_category not in config:
        return jsonify({"error": f"No templates found for {year} year"}), 404
    
    # Retrieve the templates for the selected year
    templates = []
    for template_name, template_config in config[year_category].items():
        # For each template, get the name and points (assuming points are defined in the config)
        template_data = {
            "name": template_name,
            "points": template_config.get("points", 0),  # Default to 0 if points are not specified
            "font": template_config.get("font"),
            "font_size": template_config.get("font_size"),
            "position": template_config.get("position")
        }
        templates.append(template_data)
    
    # Return the templates with name and points as a JSON response
    return jsonify({"templates": templates})

if __name__ == '__main__':
    app.run(debug=True)
