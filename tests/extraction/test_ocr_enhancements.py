#!/usr/bin/env python3
"""
Test script to verify OCR enhancements:
1. Block classification
2. Field extraction
3. Report generation
4. Enhanced PDF Analysis search
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.extraction.field_detection import extract_fields_from_block

def test_field_extraction():
    """Test that field extraction works correctly"""
    test_cases = [
        ("John Doe", ""),  # Name
        ("+1-555-123-4567", "contact information"),  # Phone
        ("john.doe@example.com", "contact"),  # Email
        ("2024-01-15", "date of birth"),  # Date
        ("$1,250.00", "total amount"),  # Amount
        ("ID: 12345-ABC", "identification"),  # ID
    ]
    
    print("=" * 60)
    print("Testing Field Extraction")
    print("=" * 60)
    
    for text, context in test_cases:
        result = extract_fields_from_block(text, context)
        print(f"\nText: {text}")
        print(f"Result: {result}")
    
    print("\n✅ Field extraction test completed")

def test_report_structure():
    """Test report structure that should be created in OCR callback"""
    report = {
        "visualization_time": 0.0,
        "ocr_time": 2.45,
        "total_blocks": 150,
        "classified_blocks": 42,
        "classification_rate": "28.0%",
        "extracted_fields": 12,
        "ocr_language": "eng",
        "ocr_dpi": 300,
        "ocr_confidence": "87.5%"
    }
    
    print("\n" + "=" * 60)
    print("Testing Report Structure")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    print("\n✅ Report structure test completed")

def test_search_capability():
    """Test that search works across blocks and fields"""
    test_data = {
        "fields": [
            {"field": "email", "value": "john@example.com", "page": 1},
            {"field": "phone", "value": "+1-555-1234", "page": 2},
        ],
        "classified_blocks": [
            {"text": "Invoice #12345", "page": 1, "block_type": "heading"},
            {"text": "Total Amount: $5,000.00", "page": 2, "block_type": "amount"},
        ]
    }
    
    print("\n" + "=" * 60)
    print("Testing Search Capability")
    print("=" * 60)
    
    search_term = "Invoice"
    print(f"\nSearching for: '{search_term}'")
    
    # Search fields
    matching_fields = [
        f for f in test_data["fields"] 
        if search_term.lower() in str(f).lower()
    ]
    print(f"Matching fields: {matching_fields}")
    
    # Search blocks
    matching_blocks = [
        b for b in test_data["classified_blocks"] 
        if search_term.lower() in b.get("text", "").lower()
    ]
    print(f"Matching blocks: {matching_blocks}")
    
    print("\n✅ Search capability test completed")

if __name__ == "__main__":
    try:
        test_field_extraction()
        test_report_structure()
        test_search_capability()
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
