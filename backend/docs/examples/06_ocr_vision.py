"""
Example 6: OCR Processing and Vision Analysis

This example demonstrates:
- Text extraction from images
- PDF to image OCR conversion
- Batch OCR processing
- Vision model analysis
- Structured data extraction
"""

import requests
import json
import base64
from pathlib import Path
from typing import Dict, Any, List
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "analyst@example.com"
PASSWORD = "password123"


def authenticate(username: str, password: str) -> str:
    """Authenticate and get JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def ocr_single_file(token: str, file_path: str) -> Dict[str, Any]:
    """
    Extract text from a single image or PDF file.

    Args:
        token: JWT access token
        file_path: Path to image or PDF file

    Returns:
        Extracted text and metadata
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (Path(file_path).name, f, "application/octet-stream")
        }

        response = requests.post(
            f"{BASE_URL}/utilities/ocr",
            headers=headers,
            files=files
        )

    response.raise_for_status()
    return response.json()


def ocr_batch(token: str, file_paths: List[str]) -> Dict[str, Any]:
    """
    Process multiple files in batch.

    Args:
        token: JWT access token
        file_paths: List of file paths

    Returns:
        Batch processing results
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    files = []
    for path in file_paths:
        with open(path, "rb") as f:
            content = f.read()
            files.append(("files", (Path(path).name, content, "application/octet-stream")))

    response = requests.post(
        f"{BASE_URL}/utilities/ocr/batch",
        headers=headers,
        files=files
    )
    response.raise_for_status()
    return response.json()


def vision_analysis(
    token: str,
    image_path: str,
    prompt: str = "Describe this image in detail"
) -> Dict[str, Any]:
    """
    Analyze image using vision model.

    Args:
        token: JWT access token
        image_path: Path to image file
        prompt: Analysis prompt

    Returns:
        Vision analysis results
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    with open(image_path, "rb") as f:
        files = {
            "image": (Path(image_path).name, f, "image/jpeg")
        }

        data = {
            "prompt": prompt
        }

        response = requests.post(
            f"{BASE_URL}/utilities/vision",
            headers=headers,
            files=files,
            data=data
        )

    response.raise_for_status()
    return response.json()


def create_sample_image_with_text(text: str, output_path: str):
    """Create a sample image with text for testing."""
    # Create image
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)

    # Add text (using default font)
    draw.text((50, 50), text, fill='black')

    # Save
    img.save(output_path)
    print(f"Created sample image: {output_path}")


def print_ocr_result(result: Dict[str, Any]):
    """Pretty print OCR result."""
    print("\n" + "="*80)
    print("OCR RESULT")
    print("="*80)

    print(f"\nFilename: {result['filename']}")
    print(f"File Type: {result['file_type']}")
    print(f"Pages Processed: {result.get('pages_processed', 1)}")
    print(f"Processing Time: {result.get('processing_time_ms', 0)/1000:.2f}s")

    if result.get('text'):
        print(f"\n--- Extracted Text ---")
        print(result['text'][:500])
        if len(result['text']) > 500:
            print(f"... ({len(result['text']) - 500} more characters)")

    if result.get('metadata'):
        print(f"\n--- Metadata ---")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")

    print("="*80 + "\n")


def print_vision_result(result: Dict[str, Any]):
    """Pretty print vision analysis result."""
    print("\n" + "="*80)
    print("VISION ANALYSIS RESULT")
    print("="*80)

    print(f"\nPrompt: {result['prompt']}")
    print(f"Model: {result['model']}")
    print(f"Processing Time: {result.get('processing_time_ms', 0)/1000:.2f}s")

    print(f"\n--- Analysis ---")
    print(result['analysis'])

    if result.get('confidence'):
        print(f"\nConfidence: {result['confidence']:.2%}")

    if result.get('objects_detected'):
        print(f"\n--- Detected Objects ---")
        for obj in result['objects_detected']:
            print(f"  • {obj['name']} ({obj['confidence']:.2%})")

    print("="*80 + "\n")


def main():
    """Main example workflow."""
    print("=" * 80)
    print("OCR & VISION PROCESSING EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[1/5] Authenticating...")
    try:
        token = authenticate(USERNAME, PASSWORD)
        print(f"✓ Successfully authenticated")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Create sample images
    print("\n[2/5] Creating sample images...")

    sample1 = Path("sample_invoice.png")
    invoice_text = """
    INVOICE #INV-2025-001

    Company Name: TechCorp Inc.
    Address: 123 Tech Street, Silicon Valley, CA 94000

    Bill To:
    Customer Name: John Doe
    Email: john@example.com

    Items:
    1. Software License - $500.00
    2. Technical Support - $200.00
    3. Training Sessions - $300.00

    Subtotal: $1,000.00
    Tax (10%): $100.00
    Total: $1,100.00

    Payment Due: January 31, 2025
    """

    create_sample_image_with_text(invoice_text, str(sample1))

    sample2 = Path("sample_receipt.png")
    receipt_text = """
    RECEIPT

    Store: SuperMart
    Date: January 15, 2025
    Time: 14:30:00

    Items:
    - Apples (2kg) - $5.00
    - Milk (1L) - $3.50
    - Bread - $2.50

    Total: $11.00
    Payment: Credit Card

    Thank you for shopping!
    """

    create_sample_image_with_text(receipt_text, str(sample2))

    # Step 3: Single file OCR
    print("\n[3/5] Processing single file with OCR...")
    try:
        ocr_result = ocr_single_file(token, str(sample1))
        print(f"✓ OCR completed successfully")
        print_ocr_result(ocr_result)
    except requests.exceptions.HTTPError as e:
        print(f"✗ OCR failed: {e}")

    # Step 4: Batch OCR processing
    print("\n[4/5] Processing multiple files with batch OCR...")
    try:
        batch_result = ocr_batch(token, [str(sample1), str(sample2)])
        print(f"✓ Batch OCR completed")
        print(f"\nProcessed {len(batch_result['results'])} files")
        print(f"Success: {batch_result['success_count']}")
        print(f"Failed: {batch_result['failed_count']}")

        for i, result in enumerate(batch_result['results'], 1):
            print(f"\n--- File {i}: {result['filename']} ---")
            if result['status'] == 'success':
                print(f"Text length: {len(result['text'])} characters")
                print(f"Preview: {result['text'][:100]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Batch OCR failed: {e}")

    # Step 5: Vision analysis
    print("\n[5/5] Analyzing image with vision model...")

    # Use the invoice image for structured extraction
    vision_prompt = """
    Analyze this invoice image and extract:
    1. Invoice number
    2. Company name
    3. Total amount
    4. Payment due date
    5. List of line items

    Format the response as structured JSON.
    """

    try:
        vision_result = vision_analysis(token, str(sample1), vision_prompt)
        print(f"✓ Vision analysis completed")
        print_vision_result(vision_result)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Vision analysis failed: {e}")

    # Cleanup
    print("\n[Cleanup] Removing sample files...")
    sample1.unlink()
    sample2.unlink()
    print(f"✓ Sample files removed")

    # Use case examples
    print("\n" + "="*80)
    print("PRACTICAL USE CASES")
    print("="*80)
    print("""
    1. Invoice Processing
       • Extract invoice details automatically
       • Store in structured format
       • Integrate with accounting systems

    2. Receipt Management
       • Digitize paper receipts
       • Track expenses
       • Generate expense reports

    3. Document Digitization
       • Convert legacy documents to searchable text
       • Build searchable archives
       • Enable full-text search

    4. Form Processing
       • Extract data from filled forms
       • Automate data entry
       • Reduce manual errors

    5. ID Verification
       • Extract information from ID cards
       • Verify identity documents
       • KYC compliance

    6. Medical Records
       • Digitize handwritten prescriptions
       • Extract patient information
       • Build medical history database

    7. License Plate Recognition
       • Parking management
       • Access control
       • Traffic monitoring

    8. Business Card Scanning
       • Extract contact information
       • Build contact database
       • CRM integration
    """)
    print("="*80)

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
OCR & VISION PROCESSING EXAMPLE
================================================================================

[1/5] Authenticating...
✓ Successfully authenticated

[2/5] Creating sample images...
Created sample image: sample_invoice.png
Created sample image: sample_receipt.png

[3/5] Processing single file with OCR...
✓ OCR completed successfully

================================================================================
OCR RESULT
================================================================================

Filename: sample_invoice.png
File Type: image/png
Pages Processed: 1
Processing Time: 1.23s

--- Extracted Text ---
INVOICE #INV-2025-001

Company Name: TechCorp Inc.
Address: 123 Tech Street, Silicon Valley, CA 94000

Bill To:
Customer Name: John Doe
Email: john@example.com

Items:
1. Software License - $500.00
2. Technical Support - $200.00
3. Training Sessions - $300.00

Subtotal: $1,000.00
Tax (10%): $100.00
Total: $1,100.00

Payment Due: January 31, 2025

--- Metadata ---
  confidence: 0.95
  language: en
  text_blocks: 15

================================================================================

[4/5] Processing multiple files with batch OCR...
✓ Batch OCR completed

Processed 2 files
Success: 2
Failed: 0

--- File 1: sample_invoice.png ---
Text length: 345 characters
Preview: INVOICE #INV-2025-001

Company Name: TechCorp Inc.
Address: 123 Tech Street, Silicon Valley, CA 94...

--- File 2: sample_receipt.png ---
Text length: 212 characters
Preview: RECEIPT

Store: SuperMart
Date: January 15, 2025
Time: 14:30:00

Items:
- Apples (2kg) - $5.00
- Mi...

[5/5] Analyzing image with vision model...
✓ Vision analysis completed

================================================================================
VISION ANALYSIS RESULT
================================================================================

Prompt: Analyze this invoice image and extract:
1. Invoice number
2. Company name
3. Total amount
4. Payment due date
5. List of line items

Format the response as structured JSON.
Model: llama3.2-vision
Processing Time: 2.45s

--- Analysis ---
Based on the image analysis, here is the extracted information:

{
  "invoice_number": "INV-2025-001",
  "company_name": "TechCorp Inc.",
  "company_address": "123 Tech Street, Silicon Valley, CA 94000",
  "bill_to": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "line_items": [
    {
      "description": "Software License",
      "amount": 500.00
    },
    {
      "description": "Technical Support",
      "amount": 200.00
    },
    {
      "description": "Training Sessions",
      "amount": 300.00
    }
  ],
  "subtotal": 1000.00,
  "tax": 100.00,
  "tax_rate": 0.10,
  "total": 1100.00,
  "payment_due_date": "2025-01-31",
  "currency": "USD"
}

Confidence: 94.23%

================================================================================

[Cleanup] Removing sample files...
✓ Sample files removed

================================================================================
PRACTICAL USE CASES
================================================================================

1. Invoice Processing
   • Extract invoice details automatically
   • Store in structured format
   • Integrate with accounting systems

2. Receipt Management
   • Digitize paper receipts
   • Track expenses
   • Generate expense reports

3. Document Digitization
   • Convert legacy documents to searchable text
   • Build searchable archives
   • Enable full-text search

4. Form Processing
   • Extract data from filled forms
   • Automate data entry
   • Reduce manual errors

5. ID Verification
   • Extract information from ID cards
   • Verify identity documents
   • KYC compliance

6. Medical Records
   • Digitize handwritten prescriptions
   • Extract patient information
   • Build medical history database

7. License Plate Recognition
   • Parking management
   • Access control
   • Traffic monitoring

8. Business Card Scanning
   • Extract contact information
   • Build contact database
   • CRM integration

================================================================================

✓ Example completed successfully!
"""
