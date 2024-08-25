import os
import json
import base64
from anthropic import Anthropic
import configparser

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '.settings'))
api_key = config['Anthropic']['api_key']
anthropic = Anthropic(api_key=api_key)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

tools = [
    {
        "name": "extract_invoice_info",
        "description": "Extracts key information from the invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string", "description": "The invoice number."},
                "invoice_date": {"type": "string", "description": "The date of the invoice."},
                "total_amount": {"type": "string", "description": "The total amount on the invoice. Don't include the $ sign"}
            },
            "required": ["invoice_number", "invoice_date", "total_amount"]
        }
    }
]

def extract_invoice_info(image_path):
    base64_image = encode_image(image_path)
    
    prompt = """
    Analyze the following invoice image and extract the following information:
    1. Invoice Number
    2. Invoice Date
    3. Total Amount

    Use the extract_invoice_info tool to provide the extracted information.  If the image is not an invoice or data missing still return using the tool with values of null.

    Here's the invoice image:
    [IMAGE]
    """

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    )

    return response

def parse_claude_response(response):
    for content in response.content:
        if content.type == 'tool_use':
            return content.input
    return None
        

def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    image_path = './InvoiceImages/CleaningInvoice.jpg'
    output_file = 'invoice_extract.json'
    
    claude_response = extract_invoice_info(image_path)
    invoice_entities = parse_claude_response(claude_response)
    save_to_json(invoice_entities, output_file)
    
    print(f"Invoice has been extracted and saved to {output_file}")
    print("Extracted Invoice:")
    print(json.dumps(invoice_entities, indent=2))

if __name__ == "__main__":
    main()