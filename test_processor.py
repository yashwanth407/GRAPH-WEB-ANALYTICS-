import pandas as pd
from data_processor import DataProcessor

# Test the file processing directly
processor = DataProcessor()

file_path = r'C:\Users\yasht\Downloads\sales_transactions_1000_with_CustomerID.csv'

try:
    print("Reading file...")
    df = pd.read_csv(file_path)
    print(f"File loaded successfully. Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"First few rows:\n{df.head()}")
    
    print("\nDetecting dataset type...")
    dataset_type = processor.detect_dataset_type(df)
    print(f"Dataset type: {dataset_type}")
    
    print("\nValidating columns...")
    validation_result = processor.validate_columns(df, dataset_type)
    print(f"Validation result: {validation_result}")
    
    if validation_result['valid']:
        print("\nCleaning data...")
        cleaned_df = processor.clean_data(df, dataset_type)
        print(f"Data cleaned successfully. Shape: {cleaned_df.shape}")
        
        print("\nCalculating KPIs...")
        data = {
            'dataset_type': dataset_type,
            'cleaned_data': cleaned_df
        }
        kpis = processor.calculate_kpis(data)
        print(f"KPIs: {kpis}")
    else:
        print(f"Validation failed: {validation_result['missing']}")
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Traceback:\n{traceback.format_exc()}")
