import pandas as pd
import os
from pathlib import Path

def read_excel_file(file_path):
    """
    Read Excel file and display all column names with their data
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found!")
            return
        
        # Read the Excel file
        print(f"Reading Excel file: {file_path}")
        print("=" * 50)
        
        # Read all sheets (in case there are multiple)
        excel_file = pd.ExcelFile(file_path)
        
        print(f"Number of sheets found: {len(excel_file.sheet_names)}")
        print(f"Sheet names: {excel_file.sheet_names}")
        print("=" * 50)
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\n📋 SHEET: {sheet_name}")
            print("-" * 40)
            
            # Read the specific sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Display basic information
            print(f"Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"Column Names: {list(df.columns)}")
            print("-" * 40)
            
            # Display column information with data types
            print("\n📊 COLUMN DETAILS:")
            for i, col in enumerate(df.columns, 1):
                non_null_count = df[col].count()
                data_type = df[col].dtype
                print(f"{i:2d}. {col:<20} | Type: {data_type:<10} | Non-null: {non_null_count}/{len(df)}")
            
            print("\n📋 FIRST 10 ROWS OF DATA:")
            print(df.head(10).to_string(index=True))
            
            # Show all data if dataset is small (less than 20 rows)
            if len(df) <= 20:
                print(f"\n📋 ALL DATA (Total {len(df)} rows):")
                print(df.to_string(index=True))
            else:
                print(f"\n📋 LAST 5 ROWS OF DATA:")
                print(df.tail(5).to_string(index=True))
            
            # Display summary statistics for numeric columns
            numeric_columns = df.select_dtypes(include=['number']).columns
            if len(numeric_columns) > 0:
                print(f"\n📈 SUMMARY STATISTICS FOR NUMERIC COLUMNS:")
                print(df[numeric_columns].describe().to_string())
            
            print("\n" + "=" * 60)
        
        # Display missing values information
        print("\n🔍 MISSING VALUES ANALYSIS:")
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                print(f"\nSheet '{sheet_name}':")
                for col, missing_count in missing_data.items():
                    if missing_count > 0:
                        percentage = (missing_count / len(df)) * 100
                        print(f"  {col}: {missing_count} missing values ({percentage:.1f}%)")
            else:
                print(f"\nSheet '{sheet_name}': No missing values found ✅")
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found!")
    except PermissionError:
        print(f"Error: Permission denied to access '{file_path}'")
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

def main():
    # Your file path
    file_path = "/home/manish/Documents/recipt_form.xlsx"
    
    print("🔍 EXCEL FILE ANALYZER")
    print("=" * 50)
    
    # Read and display the Excel file
    read_excel_file(file_path)
    
    # Optional: Interactive mode to analyze different file
    while True:
        print("\n" + "=" * 50)
        choice = input("\nDo you want to analyze another Excel file? (y/n): ").lower().strip()
        
        if choice == 'y' or choice == 'yes':
            new_file_path = input("Enter the full path to the Excel file: ").strip()
            read_excel_file(new_file_path)
        else:
            print("Thank you for using Excel File Analyzer!")
            break

if __name__ == "__main__":
    main()