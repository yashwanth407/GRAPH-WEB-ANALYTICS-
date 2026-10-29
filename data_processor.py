import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

class DataProcessor:
    def __init__(self):
        self.transaction_required_columns = [
            'TransactionID', 'CustomerID', 'ProductID', 'ProductName', 
            'Category', 'Quantity', 'Price', 'UnitPrice', 'TotalAmount', 'Date', 'SalesDate', 'PaymentMode'
        ]
        
        self.web_analytics_required_columns = [
            'SessionID', 'EventType', 'Timestamp', 'ProductID', 
            'CustomerID', 'Device', 'TrafficSource', 'SessionDuration'
        ]
    
    def process_file(self, file_path, file_ext):
        try:
            # Read the file
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                return {'error': 'Unsupported file format'}
            
            # Detect dataset type
            dataset_type = self.detect_dataset_type(df)
            
            if dataset_type == 'unknown':
                return {'error': 'Invalid Dataset: Required columns are missing. Please upload a properly formatted CSV/Excel file.'}
            
            # Validate required columns
            validation_result = self.validate_columns(df, dataset_type)
            if not validation_result['valid']:
                return {'error': f"Invalid Dataset: Missing required columns: {', '.join(validation_result['missing'])}"}
            
            # Clean the data
            cleaned_df = self.clean_data(df, dataset_type)
            
            return {
                'success': True,
                'dataset_type': dataset_type,
                'filename': file_path.split('\\')[-1],
                'cleaned_data': cleaned_df,  # Keep as DataFrame for now
                'original_data': df,  # Keep as DataFrame for now
                'column_mapping': validation_result.get('column_mapping', {})
            }
            
        except Exception as e:
            return {'error': f'Error processing file: {str(e)}'}
    
    def detect_dataset_type(self, df):
        columns = [col.strip().lower() for col in df.columns]
        
        # Check for transaction dataset with more flexible matching
        transaction_keywords = ['transaction', 'customer', 'product', 'category', 'quantity', 'price', 'amount', 'date', 'payment']
        transaction_match = sum(1 for keyword in transaction_keywords if any(keyword in col for col in columns))
        
        # Check for web analytics dataset
        web_keywords = ['session', 'event', 'timestamp', 'device', 'traffic', 'source']
        web_match = sum(1 for keyword in web_keywords if any(keyword in col for col in columns))
        
        # Prioritize transaction if it has strong indicators
        if transaction_match >= 5:
            return 'transaction'
        elif web_match >= 4:
            return 'web_analytics'
        else:
            # Default to transaction if it has basic sales indicators
            if any('total' in col or 'amount' in col for col in columns):
                return 'transaction'
            return 'unknown'
    
    def validate_columns(self, df, dataset_type):
        if dataset_type == 'transaction':
            # For transaction data, we need at least these core columns
            core_columns = ['TransactionID', 'CustomerID', 'ProductID', 'ProductName', 'Category', 'Quantity', 'TotalAmount', 'PaymentMode']
            # Date can be either 'Date' or 'SalesDate'
            # Price can be either 'Price' or 'UnitPrice'
        else:
            core_columns = self.web_analytics_required_columns
        
        available_columns = [col.strip() for col in df.columns]
        missing_columns = []
        column_mapping = {}
        
        # For transaction data, check for core columns
        if dataset_type == 'transaction':
            for required in core_columns:
                found = False
                for available in available_columns:
                    if required.lower() in available.lower() or available.lower() in required.lower():
                        column_mapping[available] = required
                        found = True
                        break
                
                if not found:
                    missing_columns.append(required)
            
            # Check for date column (Date or SalesDate)
            date_found = False
            for available in available_columns:
                if 'date' in available.lower():
                    column_mapping[available] = 'Date'
                    date_found = True
                    break
            
            if not date_found:
                missing_columns.append('Date/SalesDate')
        else:
            for required in core_columns:
                found = False
                for available in available_columns:
                    if required.lower() in available.lower() or available.lower() in required.lower():
                        column_mapping[available] = required
                        found = True
                        break
                
                if not found:
                    missing_columns.append(required)
        
        return {
            'valid': len(missing_columns) == 0,
            'missing': missing_columns,
            'column_mapping': column_mapping
        }
    
    def clean_data(self, df, dataset_type):
        cleaned_df = df.copy()
        
        # Remove duplicates
        if dataset_type == 'transaction':
            id_col = 'TransactionID'
        else:
            id_col = 'SessionID'
        
        # Find the actual column name for the ID
        id_col_actual = None
        for col in cleaned_df.columns:
            if id_col.lower() in col.lower():
                id_col_actual = col
                break
        
        if id_col_actual:
            cleaned_df = cleaned_df.drop_duplicates(subset=[id_col_actual], keep='first')
        
        # Parse dates first so missing-value fill does not destroy the original strings
        for col in cleaned_df.columns:
            if self._is_datetime_column(col):
                cleaned_df[col] = self._parse_datetime_series(cleaned_df[col])

        for col in cleaned_df.columns:
            if pd.api.types.is_datetime64_any_dtype(cleaned_df[col]):
                continue
            if cleaned_df[col].dtype in ['int64', 'float64']:
                cleaned_df[col] = cleaned_df[col].fillna(0)
            else:
                cleaned_df[col] = cleaned_df[col].fillna('Unknown')
        
        # Convert numeric columns
        numeric_columns = ['Quantity', 'Price', 'UnitPrice', 'TotalAmount', 'SessionDuration']
        for num_col in numeric_columns:
            for col in cleaned_df.columns:
                if num_col.lower() in col.lower():
                    try:
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                        cleaned_df[col] = cleaned_df[col].fillna(0)
                    except:
                        pass
        
        # Remove invalid records (negative quantities, prices)
        if dataset_type == 'transaction':
            for col in cleaned_df.columns:
                if 'quantity' in col.lower():
                    cleaned_df = cleaned_df[cleaned_df[col] >= 0]
                if 'price' in col.lower() or 'amount' in col.lower():
                    cleaned_df = cleaned_df[cleaned_df[col] >= 0]
        
        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        return cleaned_df

    def _is_datetime_column(self, column_name):
        name = str(column_name).strip().lower()
        return any(token in name for token in ('date', 'time', 'timestamp'))

    def _parse_datetime_series(self, series):
        if pd.api.types.is_datetime64_any_dtype(series):
            return series

        original = series.astype(str).str.strip()
        original = original.replace({
            '': pd.NA,
            'nan': pd.NA,
            'NaT': pd.NA,
            'None': pd.NA,
            'Unknown': pd.NA
        })
        expected = int(original.notna().sum())

        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%d-%m-%y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d-%b-%Y',
            '%d %b %Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
        ]

        best_parsed = None
        best_count = -1

        for fmt in formats:
            parsed = pd.to_datetime(original, format=fmt, errors='coerce')
            count = int(parsed.notna().sum())
            if count > best_count:
                best_count = count
                best_parsed = parsed
                if expected and best_count == expected:
                    return best_parsed

        for kwargs in (
            {'errors': 'coerce', 'dayfirst': True},
            {'errors': 'coerce', 'format': 'mixed', 'dayfirst': True},
        ):
            try:
                parsed = pd.to_datetime(original, **kwargs)
                count = int(parsed.notna().sum())
                if count > best_count:
                    best_count = count
                    best_parsed = parsed
            except TypeError:
                continue

        return best_parsed if best_parsed is not None else pd.to_datetime(original, errors='coerce')
    
    def apply_filters(self, data, filters):
        filtered_data = data.copy()
        
        # Convert dict records back to DataFrame for processing
        if isinstance(filtered_data['cleaned_data'], list):
            df = pd.DataFrame(filtered_data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
        else:
            df = filtered_data['cleaned_data'].copy()
        
        # Date range filter (start and end can be applied independently)
        if filters.get('start_date') or filters.get('end_date'):
            start_date = pd.to_datetime(filters['start_date']) if filters.get('start_date') else None
            end_date = pd.to_datetime(filters['end_date']) if filters.get('end_date') else None
            if end_date is not None:
                end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
                    if start_date is not None:
                        df = df[df[col] >= start_date]
                    if end_date is not None:
                        df = df[df[col] <= end_date]
                    break
        
        # Category filter
        if 'category' in filters and filters['category']:
            for col in df.columns:
                if 'category' in col.lower():
                    df = df[df[col].str.contains(filters['category'], case=False, na=False)]
                    break
        
        # Product filter
        if 'product' in filters and filters['product']:
            for col in df.columns:
                if 'product' in col.lower() and 'id' not in col.lower():
                    df = df[df[col].str.contains(filters['product'], case=False, na=False)]
                    break
        
        # Payment mode filter
        if 'payment_mode' in filters and filters['payment_mode']:
            for col in df.columns:
                if 'payment' in col.lower() or 'mode' in col.lower():
                    df = df[df[col].str.contains(filters['payment_mode'], case=False, na=False)]
                    break
        
        # Device filter
        if 'device' in filters and filters['device']:
            for col in df.columns:
                if 'device' in col.lower():
                    df = df[df[col].str.contains(filters['device'], case=False, na=False)]
                    break
        
        # Traffic source filter
        if 'traffic_source' in filters and filters['traffic_source']:
            for col in df.columns:
                if 'traffic' in col.lower() or 'source' in col.lower():
                    df = df[df[col].str.contains(filters['traffic_source'], case=False, na=False)]
                    break
        
        # Convert back to dict records for storage
        filtered_data['cleaned_data'] = df.to_dict('records')
        
        # Convert datetime objects to strings for JSON
        for record in filtered_data['cleaned_data']:
            for key, value in record.items():
                try:
                    if pd.isna(value):
                        record[key] = None
                        continue
                except (TypeError, ValueError):
                    pass
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        return filtered_data
    
    def calculate_kpis(self, data):
        # Convert dict records to DataFrame if needed
        if isinstance(data['cleaned_data'], list):
            df = pd.DataFrame(data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
        else:
            df = data['cleaned_data'].copy()
        
        dataset_type = data['dataset_type']
        
        kpis = {}
        
        if dataset_type == 'transaction':
            # Sales KPIs
            total_amount_col = None
            for col in df.columns:
                if 'total' in col.lower() and 'amount' in col.lower():
                    total_amount_col = col
                    break
                elif 'amount' in col.lower() and 'total' in col.lower():
                    total_amount_col = col
                    break
                elif 'amount' in col.lower():
                    total_amount_col = col
                    break
            
            if total_amount_col:
                kpis['total_sales'] = float(df[total_amount_col].sum())
            else:
                kpis['total_sales'] = 0.0
            
            kpis['total_orders'] = len(df)
            
            # Unique customers
            customer_col = None
            for col in df.columns:
                if 'customer' in col.lower() and 'id' in col.lower():
                    customer_col = col
                    break
            
            if customer_col:
                kpis['total_customers'] = df[customer_col].nunique()
            else:
                kpis['total_customers'] = 0
            
            # Average Order Value
            if kpis['total_orders'] > 0:
                kpis['aov'] = kpis['total_sales'] / kpis['total_orders']
            else:
                kpis['aov'] = 0.0
            
            # Total units sold
            quantity_col = None
            for col in df.columns:
                if 'quantity' in col.lower():
                    quantity_col = col
                    break
            
            if quantity_col:
                kpis['total_units'] = int(df[quantity_col].sum())
            else:
                kpis['total_units'] = 0
        
        elif dataset_type == 'web_analytics':
            # Web analytics KPIs
            kpis['total_visitors'] = 0
            kpis['total_sessions'] = len(df)
            kpis['page_views'] = 0
            kpis['product_views'] = 0
            kpis['add_to_cart'] = 0
            kpis['checkout_starts'] = 0
            kpis['purchases'] = 0
            
            event_type_col = None
            for col in df.columns:
                if 'event' in col.lower() and 'type' in col.lower():
                    event_type_col = col
                    break
            
            if event_type_col:
                event_counts = df[event_type_col].value_counts()
                kpis['total_visitors'] = int(event_counts.get('visit', 0))
                kpis['page_views'] = int(event_counts.get('page_view', 0))
                kpis['product_views'] = int(event_counts.get('product_view', 0))
                kpis['add_to_cart'] = int(event_counts.get('add_to_cart', 0))
                kpis['checkout_starts'] = int(event_counts.get('checkout_start', 0))
                kpis['purchases'] = int(event_counts.get('purchase', 0))
        
        return kpis
    
    def calculate_analytics(self, data):
        # Convert dict records to DataFrame if needed
        if isinstance(data['cleaned_data'], list):
            df = pd.DataFrame(data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
        else:
            df = data['cleaned_data'].copy()
        
        dataset_type = data['dataset_type']
        
        analytics = {
            'dataset_type': dataset_type,
            'total_records': len(df),
            'date_range': self.get_date_range(df),
            'categories': self.get_categories(df),
            'payment_modes': self.get_payment_modes(df),
            'devices': self.get_devices(df),
            'traffic_sources': self.get_traffic_sources(df)
        }
        
        return analytics
    
    def get_date_range(self, df):
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'timestamp' in col.lower():
                date_col = col
                break
        
        if date_col:
            dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if not dates.empty:
                return {
                    'start': dates.min().isoformat(),
                    'end': dates.max().isoformat()
                }
        return {'start': None, 'end': None}
    
    def _unique_values(self, series):
        values = []
        for value in series.dropna().unique().tolist():
            text = str(value).strip()
            if text and text.lower() != 'nan':
                values.append(text)
        return sorted(set(values))
    
    def get_categories(self, df):
        category_col = None
        for col in df.columns:
            if 'category' in col.lower():
                category_col = col
                break
        
        if category_col:
            return self._unique_values(df[category_col])
        return []
    
    def get_payment_modes(self, df):
        payment_col = None
        for col in df.columns:
            if 'payment' in col.lower() or 'mode' in col.lower():
                payment_col = col
                break
        
        if payment_col:
            return self._unique_values(df[payment_col])
        return []
    
    def get_devices(self, df):
        device_col = None
        for col in df.columns:
            if 'device' in col.lower():
                device_col = col
                break
        
        if device_col:
            return self._unique_values(df[device_col])
        return []
    
    def get_traffic_sources(self, df):
        traffic_col = None
        for col in df.columns:
            if 'traffic' in col.lower() or 'source' in col.lower():
                traffic_col = col
                break
        
        if traffic_col:
            return self._unique_values(df[traffic_col])
        return []
    
    def generate_charts(self, data, granularity='daily'):
        try:
            print("Starting generate_charts...")
            # Convert dict records to DataFrame if needed
            if isinstance(data['cleaned_data'], list):
                print("Converting list to DataFrame...")
                df = pd.DataFrame(data['cleaned_data'])
                # Convert string dates back to datetime if needed
                for col in df.columns:
                    if 'date' in col.lower() or 'timestamp' in col.lower():
                        df[col] = pd.to_datetime(df[col], errors='coerce')
            else:
                print("Using existing DataFrame...")
                df = data['cleaned_data'].copy()
            
            dataset_type = data['dataset_type']
            print(f"Dataset type: {dataset_type}")
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            charts = {}
            
            if dataset_type == 'transaction':
                charts['revenue_trend'] = self.get_revenue_trend(df, granularity)
                charts['sales_by_category'] = self.get_sales_by_category(df)
                charts['top_products'] = self.get_top_products(df)
            elif dataset_type == 'web_analytics':
                charts['conversion_funnel'] = self.get_conversion_funnel(df)
                charts['traffic_by_source'] = self.get_traffic_by_source(df)
                charts['sessions_by_device'] = self.get_sessions_by_device(df)
            
            return charts
            
        except Exception as e:
            print(f"Error in generate_charts setup: {e}")
            import traceback
            print(traceback.format_exc())
            # Return empty charts on error
            return {
                'revenue_trend': {'dates': [], 'revenue': []},
                'sales_by_category': {'categories': [], 'sales': []},
                'top_products': {'products': [], 'sales': [], 'quantities': []}
            }
    
    def get_revenue_trend(self, df, granularity='daily'):
        try:
            df = df.copy()
            date_col = None
            amount_col = None

            for col in df.columns:
                if self._is_datetime_column(col) and date_col is None:
                    date_col = col
                if 'total' in col.lower() and 'amount' in col.lower():
                    amount_col = col
                elif 'amount' in col.lower() and amount_col is None:
                    amount_col = col

            if not date_col or not amount_col:
                return {'dates': [], 'revenue': []}

            df[date_col] = self._parse_datetime_series(df[date_col])
            df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
            df = df.dropna(subset=[date_col]).sort_values(by=date_col)

            if df.empty:
                return {'dates': [], 'revenue': []}

            if granularity == 'weekly':
                grouped = df.groupby(pd.Grouper(key=date_col, freq='W'))[amount_col].sum()
                date_format = '%Y-%m-%d'
            elif granularity == 'monthly':
                try:
                    grouped = df.groupby(pd.Grouper(key=date_col, freq='ME'))[amount_col].sum()
                except ValueError:
                    grouped = df.groupby(pd.Grouper(key=date_col, freq='M'))[amount_col].sum()
                date_format = '%Y-%m'
            else:
                grouped = df.groupby(df[date_col].dt.normalize())[amount_col].sum()
                date_format = '%Y-%m-%d'

            grouped = grouped[grouped.index.notna()]
            return {
                'dates': grouped.index.strftime(date_format).tolist(),
                'revenue': [float(value) for value in grouped.tolist()]
            }
        except Exception as e:
            print(f"Error in get_revenue_trend: {e}")
            import traceback
            print(traceback.format_exc())
            return {'dates': [], 'revenue': []}
    
    def get_sales_by_category(self, df):
        try:
            print("Starting get_sales_by_category...")
            category_col = None
            amount_col = None
            
            for col in df.columns:
                if 'category' in col.lower():
                    category_col = col
                if 'total' in col.lower() and 'amount' in col.lower():
                    amount_col = col
                elif 'amount' in col.lower() and not amount_col:
                    amount_col = col
            
            print(f"Category column: {category_col}, Amount column: {amount_col}")
            
            if category_col and amount_col:
                category_sales = df.groupby(category_col)[amount_col].sum().sort_values(ascending=False)
                
                return {
                    'categories': category_sales.index.tolist(),
                    'sales': category_sales.tolist()
                }
            
            return {'categories': [], 'sales': []}
        except Exception as e:
            print(f"Error in get_sales_by_category: {e}")
            import traceback
            print(traceback.format_exc())
            return {'categories': [], 'sales': []}
    
    def get_top_products(self, df):
        try:
            print("Starting get_top_products...")
            product_col = None
            amount_col = None
            quantity_col = None
            
            for col in df.columns:
                if 'product' in col.lower() and 'name' in col.lower():
                    product_col = col
                elif 'product' in col.lower() and 'id' not in col.lower() and not product_col:
                    product_col = col
                if 'total' in col.lower() and 'amount' in col.lower():
                    amount_col = col
                elif 'amount' in col.lower() and not amount_col:
                    amount_col = col
                if 'quantity' in col.lower():
                    quantity_col = col
            
            print(f"Product column: {product_col}, Amount column: {amount_col}, Quantity column: {quantity_col}")
            
            if product_col and amount_col:
                product_stats = df.groupby(product_col).agg({
                    amount_col: 'sum',
                    quantity_col: 'sum' if quantity_col else lambda x: 0
                }).reset_index()
                
                product_stats = product_stats.sort_values(by=amount_col, ascending=False).head(20)
                
                return {
                    'products': product_stats[product_col].tolist(),
                    'sales': product_stats[amount_col].tolist(),
                    'quantities': product_stats[quantity_col].tolist() if quantity_col else [0] * len(product_stats)
                }
            
            return {'products': [], 'sales': [], 'quantities': []}
        except Exception as e:
            print(f"Error in get_top_products: {e}")
            import traceback
            print(traceback.format_exc())
            return {'products': [], 'sales': [], 'quantities': []}
    
    def get_conversion_funnel(self, df):
        event_col = None
        for col in df.columns:
            if 'event' in col.lower() and 'type' in col.lower():
                event_col = col
                break
        
        if event_col:
            event_counts = df[event_col].value_counts()
            
            funnel = {
                'visitors': int(event_counts.get('visit', 0)),
                'product_views': int(event_counts.get('product_view', 0)),
                'add_to_cart': int(event_counts.get('add_to_cart', 0)),
                'checkout_starts': int(event_counts.get('checkout_start', 0)),
                'purchases': int(event_counts.get('purchase', 0))
            }
            
            # Calculate conversion rates
            if funnel['visitors'] > 0:
                funnel['product_view_rate'] = round(funnel['product_views'] / funnel['visitors'] * 100, 2)
                funnel['add_to_cart_rate'] = round(funnel['add_to_cart'] / funnel['visitors'] * 100, 2)
                funnel['checkout_rate'] = round(funnel['checkout_starts'] / funnel['visitors'] * 100, 2)
                funnel['conversion_rate'] = round(funnel['purchases'] / funnel['visitors'] * 100, 2)
            else:
                funnel['product_view_rate'] = 0
                funnel['add_to_cart_rate'] = 0
                funnel['checkout_rate'] = 0
                funnel['conversion_rate'] = 0
            
            if funnel['add_to_cart'] > 0:
                funnel['cart_abandonment_rate'] = round((funnel['add_to_cart'] - funnel['purchases']) / funnel['add_to_cart'] * 100, 2)
            else:
                funnel['cart_abandonment_rate'] = 0
            
            return funnel
        
        return {
            'visitors': 0, 'product_views': 0, 'add_to_cart': 0,
            'checkout_starts': 0, 'purchases': 0,
            'product_view_rate': 0, 'add_to_cart_rate': 0,
            'checkout_rate': 0, 'conversion_rate': 0,
            'cart_abandonment_rate': 0
        }
    
    def get_traffic_by_source(self, df):
        source_col = None
        for col in df.columns:
            if 'traffic' in col.lower() or 'source' in col.lower():
                source_col = col
                break
        
        if source_col:
            traffic_counts = df[source_col].value_counts()
            return {
                'sources': traffic_counts.index.tolist(),
                'counts': traffic_counts.tolist()
            }
        
        return {'sources': [], 'counts': []}
    
    def get_sessions_by_device(self, df):
        device_col = None
        for col in df.columns:
            if 'device' in col.lower():
                device_col = col
                break
        
        if device_col:
            device_counts = df[device_col].value_counts()
            return {
                'devices': device_counts.index.tolist(),
                'counts': device_counts.tolist()
            }
        
        return {'devices': [], 'counts': []}
    
    def analyze_customers(self, data):
        # Convert dict records to DataFrame if needed
        if isinstance(data['cleaned_data'], list):
            df = pd.DataFrame(data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
        else:
            df = data['cleaned_data'].copy()
        
        dataset_type = data['dataset_type']
        
        if dataset_type != 'transaction':
            return {'error': 'Customer analysis only available for transaction datasets'}
        
        customer_col = None
        amount_col = None
        date_col = None
        
        for col in df.columns:
            if 'customer' in col.lower() and 'id' in col.lower():
                customer_col = col
            if 'total' in col.lower() and 'amount' in col.lower():
                amount_col = col
            elif 'amount' in col.lower() and not amount_col:
                amount_col = col
            if 'date' in col.lower():
                date_col = col
        
        if not customer_col or not amount_col:
            return {'error': 'Required columns for customer analysis not found'}
        
        # Customer spending analysis
        customer_stats = df.groupby(customer_col).agg({
            amount_col: 'sum',
            customer_col: 'count'
        }).rename(columns={customer_col: 'order_count'})
        
        customer_stats = customer_stats.sort_values(by=amount_col, ascending=False)
        
        # Customer segmentation
        total_spend = customer_stats[amount_col].sum()
        avg_spend = customer_stats[amount_col].mean()
        
        def segment_customer(row):
            spend = row[amount_col]
            orders = row['order_count']
            
            if spend >= avg_spend * 2 and orders >= 2:
                return 'High Value'
            elif spend >= avg_spend and orders >= 1:
                return 'Regular'
            elif spend >= avg_spend * 0.5:
                return 'Occasional'
            else:
                return 'Low Value'
        
        customer_stats['segment'] = customer_stats.apply(segment_customer, axis=1)
        
        # Format for response
        customers = []
        for idx, row in customer_stats.head(50).iterrows():
            customers.append({
                'customer_id': str(idx),
                'total_spend': float(row[amount_col]),
                'order_count': int(row['order_count']),
                'segment': row['segment']
            })
        
        # Segment counts
        segment_counts = {str(k): int(v) for k, v in customer_stats['segment'].value_counts().to_dict().items()}
        
        return {
            'customers': customers,
            'segment_counts': segment_counts,
            'total_customers': len(customer_stats)
        }
    
    def analyze_web_analytics(self, data):
        # Convert dict records to DataFrame if needed
        if isinstance(data['cleaned_data'], list):
            df = pd.DataFrame(data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if self._is_datetime_column(col):
                    df[col] = self._parse_datetime_series(df[col])
        else:
            df = data['cleaned_data'].copy()
        
        dataset_type = data['dataset_type']
        
        if dataset_type != 'web_analytics':
            return {'error': 'Web analytics only available for web analytics datasets'}
        
        funnel = self.get_conversion_funnel(df)
        traffic = self.get_traffic_by_source(df)
        devices = self.get_sessions_by_device(df)
        
        return {
            'funnel': funnel,
            'traffic_by_source': traffic,
            'sessions_by_device': devices
        }
