import pandas as pd
import json
from datetime import datetime
import os

def process_excel_for_receipts(file_path):
    """
    Process Excel file and prepare data for bulk PDF receipt generation
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        print(f"📊 EXCEL DATA ANALYSIS")
        print(f"=" * 50)
        print(f"Total Rows: {df.shape[0]}")
        print(f"Total Columns: {df.shape[1]}")
        
        # Required columns for receipt generation
        required_columns = [
            'user_id', 'firstname', 'father', 'gotra',
            'user_address_type', 'user_tehsil', 'user_district', 'user_state',
            'mobile_number_1', 'vyaapar_name', 'vyaapar_type', 'vyaapar_tehsil'
        ]
        
        print(f"\n📋 COLUMN MAPPING FOR RECEIPTS:")
        print(f"-" * 50)
        
        available_columns = []
        missing_columns = []
        
        for col in required_columns:
            if col in df.columns:
                available_columns.append(col)
                print(f"✅ {col:<20} -> Available")
            else:
                missing_columns.append(col)
                print(f"❌ {col:<20} -> Missing")
        
        if missing_columns:
            print(f"\n⚠️  WARNING: {len(missing_columns)} required columns are missing!")
            print(f"Missing columns: {missing_columns}")
        
        # Clean and prepare data for receipts
        receipt_data = []
        
        print(f"\n🔄 PROCESSING DATA FOR RECEIPTS:")
        print(f"-" * 50)
        
        current_date = datetime.now()
        formatted_date = current_date.strftime('%d/%m/%Y')
        formatted_datetime = current_date.strftime('%Y-%m-%d %H:%M:%S')
        
        for index, row in df.iterrows():
            # Clean each record
            clean_record = {}
            
            for col in required_columns:
                if col in df.columns:
                    value = row[col]
                    # Handle NaN, None, and empty values
                    if pd.isna(value) or value is None or str(value).strip() == '':
                        clean_record[col] = ''
                    else:
                        clean_record[col] = str(value).strip()
                else:
                    clean_record[col] = ''
            
            # Override user_id with sequential number starting from 1
            clean_record['user_id'] = str(index + 1)
            clean_record['original_user_id'] = clean_record.get('user_id', '') if 'user_id' in df.columns else ''
            
            # Add additional info
            clean_record['receipt_number'] = index + 1
            clean_record['serial_number'] = index + 1
            clean_record['generation_date'] = formatted_datetime
            clean_record['receipt_date'] = formatted_date
            clean_record['current_date'] = formatted_date
            
            receipt_data.append(clean_record)
            
            # Show progress for large files
            if (index + 1) % 100 == 0:
                print(f"Processed {index + 1} records...")
        
        print(f"✅ Successfully processed {len(receipt_data)} records")
        
        # Display sample records
        show_sample_data(receipt_data)
        
        # Save processed data to JSON for easy access
        save_processed_data(receipt_data, file_path)
        
        # Generate summary report
        generate_summary_report(receipt_data, df)
        
        return receipt_data
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {str(e)}")
        return []

def show_sample_data(receipt_data, num_samples=3):
    """
    Display sample processed data
    """
    print(f"\n📄 SAMPLE PROCESSED DATA (First {num_samples} records):")
    print(f"=" * 80)
    
    for i in range(min(num_samples, len(receipt_data))):
        record = receipt_data[i]
        print(f"\n--- RECORD {i + 1} ---")
        print(f"Serial Number: {record['serial_number']}")
        print(f"User ID: {record['user_id']} (Original: {record.get('original_user_id', 'N/A')})")
        print(f"Name: {record['firstname']}")
        print(f"Father: {record['father']}")
        print(f"Gotra: {record['gotra']}")
        print(f"Address: {record['user_address_type']}, {record['user_tehsil']}, {record['user_district']}, {record['user_state']}")
        print(f"Mobile: {record['mobile_number_1']}")
        print(f"Business: {record['vyaapar_name']} ({record['vyaapar_type']})")
        print(f"Business Address: {record['vyaapar_tehsil']}")
        print(f"Receipt Date: {record['current_date']}")
        print(f"Generated: {record['generation_date']}")
        print("-" * 40)

def save_processed_data(receipt_data, original_file_path):
    """
    Save processed data to JSON file for easy loading in React
    """
    try:
        # Create output filename
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = f"{base_name}_processed_receipts.json"
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(receipt_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 SAVED PROCESSED DATA:")
        print(f"File: {output_file}")
        print(f"Records: {len(receipt_data)}")
        print(f"Size: {os.path.getsize(output_file)} bytes")
        
    except Exception as e:
        print(f"❌ Error saving processed data: {str(e)}")

def generate_summary_report(receipt_data, original_df):
    """
    Generate a summary report of the data processing
    """
    print(f"\n📊 SUMMARY REPORT:")
    print(f"=" * 50)
    
    # Count non-empty fields
    field_stats = {}
    for field in ['user_id', 'firstname', 'father', 'gotra', 'mobile_number_1', 'vyaapar_name']:
        non_empty = sum(1 for record in receipt_data if record[field] != '')
        field_stats[field] = {
            'filled': non_empty,
            'empty': len(receipt_data) - non_empty,
            'percentage': (non_empty / len(receipt_data)) * 100
        }
    
    print(f"Field Completion Status:")
    for field, stats in field_stats.items():
        print(f"  {field:<20}: {stats['filled']:>4}/{len(receipt_data)} ({stats['percentage']:>5.1f}%)")
    
    # Identify records with missing critical data
    critical_fields = ['user_id', 'firstname', 'mobile_number_1']
    incomplete_records = []
    
    for i, record in enumerate(receipt_data):
        missing_critical = [field for field in critical_fields if record[field] == '']
        if missing_critical:
            incomplete_records.append({
                'index': i + 1,
                'user_id': record['user_id'],
                'missing': missing_critical
            })
    
    if incomplete_records:
        print(f"\n⚠️  RECORDS WITH MISSING CRITICAL DATA:")
        print(f"Total incomplete records: {len(incomplete_records)}")
        for record in incomplete_records[:5]:  # Show first 5
            print(f"  Record {record['index']}: ID={record['user_id']}, Missing: {record['missing']}")
        if len(incomplete_records) > 5:
            print(f"  ... and {len(incomplete_records) - 5} more")
    else:
        print(f"\n✅ All records have critical data (user_id, firstname, mobile_number_1)")

def generate_bulk_receipts_html(receipt_data):
    """
    Generate HTML file for bulk receipt printing
    """
    try:
        html_template = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk Receipt Generation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .receipt-container { 
            max-width: 800px; margin: 20px auto; padding: 20px; 
            border: 3px solid #000; background-color: #fff; 
            page-break-after: always; min-height: 100vh;
        }
        .receipt-border { padding: 15px; }
        .header-text { 
            display: flex; justify-content: space-between; 
            margin-bottom: 15px; font-size: 14px; font-weight: bold; 
        }
        .center-mantra { text-align: center; }
        .main-header { 
            display: flex; align-items: center; justify-content: space-between; 
            margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 15px; 
        }
        .left-logo, .right-logo { 
            width: 80px; height: 80px; border: 1px solid #ccc; 
            display: flex; align-items: center; justify-content: center; 
            background-color: #f0f0f0; font-size: 10px; text-align: center;
        }
        .center-title { text-align: center; flex: 1; margin: 0 20px; }
        .center-title h1 { font-size: 22px; font-weight: bold; margin: 0 0 5px 0; }
        .receipt-header { 
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 20px; font-size: 16px; font-weight: bold; 
        }
        .personal-info { margin-bottom: 20px; }
        .info-row { display: flex; margin-bottom: 15px; }
        .info-item { flex: 1; margin-right: 20px; }
        .info-item:last-child { margin-right: 0; }
        .label { font-weight: bold; }
        .value { 
            border-bottom: 1px solid #000; min-width: 200px; 
            display: inline-block; padding-bottom: 2px; 
        }
        .office-address .value { min-width: 600px; }
        .payment-section { margin-bottom: 25px; }
        .payment-text { font-size: 16px; font-weight: bold; margin-bottom: 20px; }
        .payment-options { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .payment-option { display: flex; align-items: center; }
        .payment-option span { margin-right: 10px; font-weight: bold; }
        .checkbox { width: 25px; height: 25px; border: 2px solid #000; }
        .utr-box { width: 200px; height: 30px; border: 2px solid #000; }
        .bottom-section { display: flex; justify-content: space-between; align-items: end; }
        .amount-box { 
            border: 3px solid #000; padding: 20px 30px; font-size: 28px; 
            font-weight: bold; background-color: #f8f8f8; 
        }
        .signatures { display: flex; gap: 120px; }
        .signature { text-align: center; }
        .signature div { 
            width: 180px; border-top: 2px solid #000; padding-top: 8px; 
            font-size: 16px; font-weight: bold; 
        }
        @media print {
            @page { size: A4; margin: 0.5in; }
            .no-print { display: none; }
        }
    </style>
</head>
<body>
    <div class="no-print" style="position: fixed; top: 10px; right: 10px; background: white; padding: 20px; border: 2px solid #ccc; border-radius: 10px; z-index: 1000;">
        <h3>Bulk Receipt Generator</h3>
        <p>Total Receipts: {total_receipts}</p>
        <button onclick="window.print()" style="background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
            Print All Receipts
        </button>
    </div>

{receipts_html}

</body>
</html>
        """
        
        receipts_html = ""
        current_date = datetime.now().strftime('%d/%m/%Y')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        for i, record in enumerate(receipt_data):
            # Clean function for individual values
            def clean_value(value):
                if not value or str(value).strip() == '' or str(value).strip().lower() == 'nan':
                    return ''
                return str(value).strip()
            
            # Use the sequential user ID and current date from record
            sequential_user_id = record['user_id']  # This is now 1, 2, 3, etc.
            receipt_date = record.get('current_date', current_date)
            
            # Combine address
            address_parts = [
                clean_value(record['user_address_type']),
                clean_value(record['user_tehsil']),
                clean_value(record['user_district']),
                clean_value(record['user_state'])
            ]
            full_address = ', '.join([part for part in address_parts if part])
            
            receipt_html = f"""
    <div class="receipt-container">
        <div class="receipt-border">
            <div class="header-text">
                <div class="left-mantra">।। श्री आईजी प्रसादत् ।।</div>
                <div class="center-mantra">
                    ।। श्री गणेशाय नमः ।।<br>
                    देवी सर्व भूतेषु। ज्योती रूपेण संस्तिथा नमत्सये नमत्सये नमत्सये ।।।। नमोः नमः ।।
                </div>
                <div class="right-mantra">।। श्री कुलदेवताय नमः ।।</div>
            </div>

            <div class="main-header">
                <div class="left-logo">LOGO</div>
                <div class="center-title">
                    <h1>श्री सीरवी समाज कर्नाटक ट्रस्ट (रजि.)</h1>
                    <div style="font-size: 14px; margin: 5px 0;">116, जे. एम. लेन, बलेपेट, बेंगलोर 560053</div>
                    <div style="font-size: 12px; margin: 5px 0;">PH: 080-22876090, Mob: +91 9019905115/+91 90199 06116</div>
                    <div style="font-size: 12px; margin: 5px 0;">Email: seervisamajkarnataka@gmail.com</div>
                    <div style="font-size: 10px; margin: 5px 0;">Regd.No.: DIT (E) BLR/12A/S-2409/AALTS1631E/ITO(E)-3 VIL 2012-13</div>
                </div>
                <div class="right-logo">MATAJI</div>
            </div>

            <div class="receipt-details">
                <div class="receipt-header">
                    <div class="serial-number">यूजर आईडी: {sequential_user_id}</div>
                    <div class="receipt-title">वार्षिक शुल्क पावती 2024</div>
                    <div class="date">दिनांक: {receipt_date}</div>
                </div>

                <div class="personal-info">
                    <div class="info-row">
                        <div class="info-item">
                            <span class="label">नाम श्री: </span>
                            <span class="value">{clean_value(record['firstname'])}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">पिताजी का नाम श्री: </span>
                            <span class="value">{clean_value(record['father'])}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-item">
                            <span class="label">गोत्र: </span>
                            <span class="value">{clean_value(record['gotra'])}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">मो नं: </span>
                            <span class="value">{clean_value(record['mobile_number_1'])}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-item" style="width: 100%;">
                            <span class="label">मूलनिवास: </span>
                            <span class="value" style="min-width: 500px;">{full_address}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-item">
                            <span class="label">कार्यालय का नाम: </span>
                            <span class="value">{clean_value(record['vyaapar_name'])}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">कार्यालय का प्रकार: </span>
                            <span class="value">{clean_value(record['vyaapar_type'])}</span>
                        </div>
                    </div>

                    <div class="office-address" style="margin-bottom: 20px;">
                        <span class="label">कार्यालय का पता: </span>
                        <span class="value">{clean_value(record['vyaapar_tehsil'])}</span>
                    </div>
                </div>

                <div class="payment-section">
                    <div class="payment-text">आपसे तीन हजार एक सो रुपये मात्र सधन्यवाद प्राप्त हुए</div>
                    <div class="payment-options">
                        <div class="payment-option">
                            <span>Cash</span>
                            <div class="checkbox"></div>
                        </div>
                        <div class="payment-option">
                            <span>Bank</span>
                            <div class="checkbox"></div>
                        </div>
                        <div class="payment-option">
                            <span>UTR No:</span>
                            <div class="utr-box"></div>
                        </div>
                    </div>
                </div>

                <div class="bottom-section">
                    <div class="amount-box">
                        <span class="rupee-symbol">₹</span>
                        <span class="amount">3100/-</span>
                    </div>
                    <div class="signatures">
                        <div class="signature">
                            <div>ह. दानदाता</div>
                        </div>
                        <div class="signature">
                            <div>ह. प्राप्तकर्ता</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
            """
            receipts_html += receipt_html
        
        # Generate final HTML
        final_html = html_template.format(
            total_receipts=len(receipt_data),
            receipts_html=receipts_html
        )
        
        # Save HTML file
        output_filename = "bulk_receipts.html"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"\n📄 BULK RECEIPTS HTML GENERATED:")
        print(f"File: {output_filename}")
        print(f"Receipts: {len(receipt_data)}")
        print(f"Size: {os.path.getsize(output_filename)} bytes")
        print(f"\n💡 Open '{output_filename}' in browser and print to generate all PDFs!")
        
        return output_filename
        
    except Exception as e:
        print(f"❌ Error generating bulk receipts HTML: {str(e)}")
        return None

def main():
    """
    Main function to process Excel and generate receipts
    """
    file_path = "/home/manish/Documents/recipt_form.xlsx"
    
    print("🎯 BULK RECEIPT GENERATOR")
    print("=" * 60)
    print(f"Processing file: {file_path}")
    print()
    
    # Process Excel data
    receipt_data = process_excel_for_receipts(file_path)
    
    if receipt_data:
        # Generate bulk HTML receipts
        html_file = generate_bulk_receipts_html(receipt_data)
        
        print(f"\n🎉 SUCCESS!")
        print(f"=" * 30)
        print(f"✅ Processed {len(receipt_data)} records")
        print(f"✅ Generated JSON data file")
        print(f"✅ Generated HTML bulk receipts")
        print(f"\n📝 Next Steps:")
        print(f"1. Open '{html_file}' in your browser")
        print(f"2. Click 'Print All Receipts' button")
        print(f"3. Select 'Save as PDF' or print to physical printer")
        print(f"4. All {len(receipt_data)} receipts will be generated!")
        
    else:
        print(f"\n❌ Failed to process Excel file")

if __name__ == "__main__":
    main()