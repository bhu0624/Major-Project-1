products = {
    '123456789012': {'name': 'Product A', 'weight': 100, 'price': 10.99},
    '987654321098': {'name': 'Product B', 'weight': 200, 'price': 15.49},
    # Add more products as needed
}

cart = []

def get_product_info(barcode_data):
    if barcode_data in products:
        return products[barcode_data]
    return None

def add_to_cart(product_info):
    cart.append(product_info)

def remove_from_cart(barcode_data):
    for item in cart:
        if item['barcode_data'] == barcode_data:
            cart.remove(item)
            break

def get_cart_data():
    return [{'name': item['name'], 'quantity': 1, 'price': item['price']} for item in cart]

def generate_bill():
    total = sum(item['price'] for item in cart)
    html = '<h2>Bill</h2>'
    html += '<table>'
    html += '<tr><th>Product</th><th>Quantity</th><th>Price</th></tr>'
    for item in cart:
        html += f'<tr><td>{item["name"]}</td><td>1</td><td>${item["price"]}</td></tr>'
    html += f'<tr><td colspan="2">Total:</td><td>${total:.2f}</td></tr>'
    html += '</table>'
    return html