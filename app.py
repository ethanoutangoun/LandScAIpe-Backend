from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
import io
import base64
import os

import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


app = Flask(__name__)
CORS(app)

def convert_to_black_and_white(input_image_bytes):
    # Convert the image to black and white
    image = Image.open(io.BytesIO(input_image_bytes))
    image_bw = image.convert("L")

    # Save the black and white image to bytes
    output_image_bytes = io.BytesIO()
    image_bw.save(output_image_bytes, format="JPEG")
    return output_image_bytes.getvalue()

@app.route('/api/data', methods=['GET'])
def get_data():
    data = {'message': 'Hello from Flask!'}
    return jsonify(data)



@app.route('/api/process', methods=['POST'])
def process_image():
    try:
        data = request.get_json()


        image_data = data['image']

        # Decode base64-encoded image data
        try:
            image_binary = base64.b64decode(image_data.split(',')[1])
        except Exception as e:
            return jsonify({'error': 'Invalid image data format'}), 400
        


        # # Save the original image to the server directory
        # original_image_filename = 'received_image.png'
        # with open(original_image_filename, 'wb') as original_image_file:
        #     original_image_file.write(image_binary)




        # Convert the image to black and white
        output_image_bytes = convert_to_black_and_white(image_binary)

        # Save the black and white image to a file
        # output_image_filename = 'output.jpg'
        # with open(output_image_filename, 'wb') as output_image_file:
        #     output_image_file.write(output_image_bytes)

     
       
        # Encode the black and white image data as base64
        base64_output = base64.b64encode(output_image_bytes).decode('utf-8')

        # Return the base64-encoded black and white image in the response
        return jsonify({'image': base64_output})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})


@app.route('/api/nativeplants/<zipcode>', methods=['GET'])
def getNativePlants(zipcode):
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    
    url = f'https://www.audubon.org/native-plants/search?zipcode={zipcode}'

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    data = []

   

    while True:
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "custom-h3")))
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')


        custom_h3_tags = soup.find_all('h2', class_='custom-h3')
        latin_names = soup.find_all('h3', class_='scientific-title custom-h4')
        tier_1_descriptions = soup.find_all('div', class_='tier-1-plant--description')
        plant_images = soup.find_all('button', class_='tier-1-plant-picture-modal cboxElement')

        for plant,latin, description, plant_image in zip(custom_h3_tags, latin_names, tier_1_descriptions, plant_images):
            # print(f"Plant: {plant.text.strip()} ({latin.text.strip()})")
            # print(f"Description: {description.text.strip()}\n")
            # print(f"Image: {plant_image['data-href']}\n")

            plant_data = {
                "Plant": plant.text.strip(),
                "Latin Name": latin.text.strip(),
                "Description": description.text.strip(),
                "Image": plant_image['data-href']
            }

            data.append(plant_data)
        
        try:
            next_button = driver.find_element(By.XPATH, "//a[@title='Go to next page' and @rel='next']")
            driver.execute_script("arguments[0].click();", next_button)
        except:
            break

 

    
    driver.quit()

    return jsonify(data)





if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)
