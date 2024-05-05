from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import cv2
import pyzbar.pyzbar as pyzbar
from database import get_product_info, add_to_cart, remove_from_cart, get_cart_data, generate_bill
import time
import qrcode
import io

app = Flask(__name__)



# Configure GPIO pins
GPIO.setmode(GPIO.BCM)
BUZZER_PIN = 18
CAMERA_PIN = 23
LOAD_CELL_PIN = 24
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(CAMERA_PIN, GPIO.OUT)
GPIO.setup(LOAD_CELL_PIN, GPIO.IN)



# Initialize camera
cap = cv2.VideoCapture(0)



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    # Activate camera
    GPIO.output(CAMERA_PIN, GPIO.HIGH)

    # Capture frame from the camera
    ret, frame = cap.read()

    # Decode barcodes from the frame
    barcodes = pyzbar.decode(frame)

    if barcodes:
        barcode_data = barcodes[0].data.decode('utf-8')

        # Get product information from the database
        product_info = get_product_info(barcode_data)

        if product_info:
            # Verify weight
            expected_weight = product_info['weight']
            actual_weight = read_load_cell()

            if abs(expected_weight - actual_weight) < 20:  # Allow a tolerance of 20 grams
                # Add the product to the cart
                add_to_cart(product_info)
                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'barcode_data': barcode_data, 'status': 'success'})
            else:
                # Weight mismatch
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'status': 'error', 'message': 'Weight mismatch'})

    GPIO.output(CAMERA_PIN, GPIO.LOW)
    return jsonify({'status': 'error', 'message': 'Barcode not detected'})



@app.route('/add_multiple_items', methods=['POST'])
def add_multiple_items():
    # Activate camera
    GPIO.output(CAMERA_PIN, GPIO.HIGH)

    # Capture frame from the camera
    ret, frame = cap.read()

    # Decode barcodes from the frame
    barcodes = pyzbar.decode(frame)

    if barcodes:
        barcode_data = barcodes[0].data.decode('utf-8')

        # Get product information from the database
        product_info = get_product_info(barcode_data)

        if product_info:
            # Get the quantity from the user
            quantity = request.form.get('quantity', type=int)

            # Calculate the expected total weight
            expected_total_weight = product_info['weight'] * quantity

            # Read the actual weight from the load cell
            actual_weight = read_load_cell()

            if abs(expected_total_weight - actual_weight) < 20:  # Allow a tolerance of 20 grams
                # Add the product to the cart multiple times
                for _ in range(quantity):
                    add_to_cart(product_info)

                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'status': 'success'})
            else:
                # Weight mismatch
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'status': 'error', 'message': 'Weight mismatch'})

    GPIO.output(CAMERA_PIN, GPIO.LOW)
    return jsonify({'status': 'error', 'message': 'Barcode not detected'})



@app.route('/remove_item', methods=['POST'])
def remove_item():
    # Activate camera
    GPIO.output(CAMERA_PIN, GPIO.HIGH)

    # Capture frame from the camera
    ret, frame = cap.read()

    # Decode barcodes from the frame
    barcodes = pyzbar.decode(frame)

    if barcodes:
        barcode_data = barcodes[0].data.decode('utf-8')

        # Get product information from the database
        product_info = get_product_info(barcode_data)

        if product_info:
            # Remove the item from the cart
            remove_from_cart(barcode_data)

            # Get updated cart data
            cart_data = get_cart_data()

            # Calculate expected total weight
            expected_total_weight = sum(item['weight'] for item in cart_data)
            actual_weight = read_load_cell()

            if abs(expected_total_weight - actual_weight) < 20:  # Allow a tolerance of 20 grams
                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'cart_data': cart_data, 'status': 'success'})
            else:
                # Weight mismatch
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                GPIO.output(CAMERA_PIN, GPIO.LOW)
                return jsonify({'status': 'error', 'message': 'Weight mismatch'})

    GPIO.output(CAMERA_PIN, GPIO.LOW)
    return jsonify({'status': 'error', 'message': 'Barcode not detected'})



@app.route('/generate_bill', methods=['GET'])
def generate_bill():
    # Generate the bill HTML
    bill_html, total_amount = generate_bill()

    # Generate QR code for payment
    qr_code = generate_qr_code(total_amount)

    return jsonify({'bill_html': bill_html, 'qr_code': qr_code})



def read_load_cell():
    # Read weight from the load cell connected to the GPIO pin
    # Replace with your actual code to read the load cell
    # Read weight from the load cell connected to the GPIO pin
    weight = 0
    try:
        # Your code to read the load cell input and store the weight value
        # Example:
        weight = GPIO.input(LOAD_CELL_PIN)
    except Exception as e:
        print(f"Error reading load cell: {e}")
    return weight



def generate_qr_code(amount):
    # Generate a QR code for the given amount
    # Replace with your actual code to generate the QR code
    #return 'https://example.com/payment?amount=' + str(amount)
    # Generate a QR code for the given amount
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"https://example.com/payment?amount={amount}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io.read()



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)