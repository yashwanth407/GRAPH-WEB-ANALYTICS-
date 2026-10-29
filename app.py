from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import uuid
from datetime import datetime
from data_processor import DataProcessor

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# In-memory storage for processed data
processed_data_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        print("Upload request received")
        
        if 'file' not in request.files:
            print("No file in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            print(f"Invalid file format: {file.filename}")
            return jsonify({'error': 'Invalid file format. Please upload CSV or Excel files only.'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        print(f"Session ID: {session_id}")
        
        # Save file temporarily
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        temp_filename = f"{session_id}.{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        print(f"Saving file to: {file_path}")
        
        # Ensure upload directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            print(f"Created upload directory: {app.config['UPLOAD_FOLDER']}")
        
        file.save(file_path)
        print("File saved successfully")
        
        # Process the file
        print("Processing file...")
        processor = DataProcessor()
        result = processor.process_file(file_path, file_ext)
        print(f"Processing result: {result}")
        
        # Clean up temporary file
        try:
            os.remove(file_path)
            print("Temporary file removed")
        except Exception as cleanup_error:
            print(f"Error removing temp file: {cleanup_error}")
        
        if result.get('error'):
            print(f"Processing error: {result['error']}")
            return jsonify(result), 400
        
        # Store processed data in memory (convert DataFrame to dict for JSON serialization)
        # Convert Timestamp objects to strings for JSON compatibility
        cleaned_data_dict = result['cleaned_data'].to_dict('records')
        for record in cleaned_data_dict:
            for key, value in record.items():
                try:
                    if pd.isna(value):
                        record[key] = None
                        continue
                except (TypeError, ValueError):
                    pass
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        stored_data = {
            'dataset_type': result['dataset_type'],
            'filename': result['filename'],
            'cleaned_data': cleaned_data_dict,
            'column_mapping': result.get('column_mapping', {})
        }
        processed_data_store[session_id] = stored_data
        print("Data stored in memory")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'dataset_type': result['dataset_type'],
            'message': 'File processed successfully'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing file: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error processing file: {str(e)}', 'details': error_details}), 500

@app.route('/api/analytics/<session_id>', methods=['GET'])
def get_analytics(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        processor = DataProcessor()
        
        # Apply filters if provided
        filters = request.args.to_dict()
        if filters:
            data = processor.apply_filters(data, filters)
        
        analytics = processor.calculate_analytics(data)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating analytics: {str(e)}'}), 500

@app.route('/api/kpis/<session_id>', methods=['GET'])
def get_kpis(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        processor = DataProcessor()
        
        # Apply filters if provided
        filters = request.args.to_dict()
        if filters:
            data = processor.apply_filters(data.copy(), filters)
        
        kpis = processor.calculate_kpis(data)
        
        return jsonify({
            'success': True,
            'kpis': kpis
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error calculating KPIs: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error calculating KPIs: {str(e)}', 'details': error_details}), 500

@app.route('/api/charts/<session_id>', methods=['GET'])
def get_charts(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        processor = DataProcessor()

        filters = request.args.to_dict()
        granularity = filters.pop('granularity', 'daily')

        if filters:
            data = processor.apply_filters(data.copy(), filters)
        
        charts = processor.generate_charts(data, granularity)
        
        return jsonify({
            'success': True,
            'charts': charts
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating charts: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error generating charts: {str(e)}', 'details': error_details}), 500

@app.route('/api/customers/<session_id>', methods=['GET'])
def get_customers(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        processor = DataProcessor()
        
        # Apply filters if provided
        filters = request.args.to_dict()
        if filters:
            data = processor.apply_filters(data.copy(), filters)
        
        customers = processor.analyze_customers(data)
        
        return jsonify({
            'success': True,
            'customers': customers
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error analyzing customers: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error analyzing customers: {str(e)}', 'details': error_details}), 500

@app.route('/api/web-analytics/<session_id>', methods=['GET'])
def get_web_analytics(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        processor = DataProcessor()
        
        # Apply filters if provided
        filters = request.args.to_dict()
        if filters:
            data = processor.apply_filters(data.copy(), filters)
        
        web_analytics = processor.analyze_web_analytics(data)
        
        return jsonify({
            'success': True,
            'web_analytics': web_analytics
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error analyzing web analytics: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': f'Error analyzing web analytics: {str(e)}', 'details': error_details}), 500

@app.route('/api/data-preview/<session_id>', methods=['GET'])
def get_data_preview(session_id):
    if session_id not in processed_data_store:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = processed_data_store[session_id]
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Convert dict records to DataFrame if needed
        if isinstance(data['cleaned_data'], list):
            df = pd.DataFrame(data['cleaned_data'])
            # Convert string dates back to datetime if needed
            for col in df.columns:
                if 'date' in col.lower() or 'timestamp' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        else:
            df = data['cleaned_data']
        
        total_rows = len(df)
        total_pages = (total_rows + per_page - 1) // per_page
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        page_data = df.iloc[start_idx:end_idx].to_dict('records')
        
        # Convert datetime objects to strings for JSON
        for record in page_data:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        return jsonify({
            'success': True,
            'filename': data['filename'],
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'dataset_type': data['dataset_type'],
            'data': page_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_rows': total_rows
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting data preview: {str(e)}'}), 500

@app.route('/api/sample/<dataset_type>', methods=['GET'])
def get_sample_file(dataset_type):
    samples = {
        'transaction': 'sample_transaction_data.csv',
        'web': 'sample_web_analytics_data.csv'
    }
    filename = samples.get(dataset_type)
    if not filename:
        return jsonify({'error': 'Unknown sample dataset'}), 404

    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(sample_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Sample file not found'}), 404

    return send_from_directory(sample_dir, filename, as_attachment=True, mimetype='text/csv')


@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_id in processed_data_store:
        del processed_data_store[session_id]
        return jsonify({'success': True, 'message': 'Session deleted'})
    return jsonify({'error': 'Session not found'}), 404

# Serve React app for all non-API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
