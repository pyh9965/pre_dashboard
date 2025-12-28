import pandas as pd

file_path = '설문조사 DB/DEFINE_DB.xlsx'

# Check all sheets
xl_file = pd.ExcelFile(file_path)
print(f'Sheet names: {xl_file.sheet_names}')
print()

# Check each sheet
for sheet_name in xl_file.sheet_names:
    print(f'=== Sheet: {sheet_name} ===')
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f'Rows: {len(df)}, Columns: {len(df.columns)}')
    
    # Check if there's actual data (non-NaN values)
    non_null_count = df.notna().sum().sum()
    print(f'Non-null cells: {non_null_count}')
    
    if non_null_count > 0:
        print('\nFirst few column names:')
        for i, col in enumerate(df.columns[:10]):
            print(f'  [{i}]: {col}')
        
        print('\nFirst row sample (non-null):')
        first_row = df.iloc[0]
        for i, val in enumerate(first_row[:10]):
            if pd.notna(val):
                print(f'  Col {i}: {val}')
    
    print()
