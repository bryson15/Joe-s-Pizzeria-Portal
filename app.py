from flask import Flask, Response, abort, render_template, request, jsonify
import main
import atexit

app = Flask(__name__)

try:
    main.Main()
except Exception as e:
    try:
        main.Main()
    except Exception as e:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pdf/<path:pdf_name>')
def pdf_path(pdf_name):
    pdf_data = main.Main().get_pdf(pdf_name)
    response = Response(pdf_data, content_type='application/pdf')
    if not pdf_data:
        abort(404, description="PDF not found")
    return response

@app.route('/dockets/<path:order_id>')
def dockets_path(order_id):
    docket = main.Main().get_document("dockets", int(order_id))
    if not docket:
        abort(404, description="Docket not found")
    if '_id' in docket:
        docket['_id'] = str(docket['_id'])
    return jsonify(docket)

@app.route('/transactions/<path:order_id>')
def transactions_path(order_id):
    transaction = main.Main().get_document("transactions", int(order_id))
    if not transaction:
        abort(404, description="Transaction not found")
    if '_id' in transaction:
        transaction['_id'] = str(transaction['_id'])
    return jsonify(transaction)

@app.route('/import', methods=['GET', 'POST'])
def import_page(): 
    result = None
    error = None
    selected_date = None
    if request.method == 'POST':
        selected_date = request.form['selected_date']
        result, error = main.Main().import_transactions(selected_date)
    return render_template('import.html', result=result, error=error, selected_date=selected_date)

@app.route('/input')
def input_page():   
    items = main.Main().get_distinct_items()
    print (items)
    return render_template('input.html', items=items)

@app.route('/postcode_input', methods=['POST'])
def postcode_input():
    post_code = int(request.form['postcode'])
    result = main.Main().get_driver_by_post_code(post_code)
    if (result): 
        return jsonify({'driver_id': result['driver_id'], 'commission_rate': result['commission_rate']})
    else:
        return jsonify({'error': f'No drivers deliver to postcode {post_code}'})
    
@app.route('/submit_input', methods=['POST'])
def submit_input():
    result, error = main.Main().submit_input(request.form)
    return jsonify({"error": error, "result": result})

@app.route('/report', methods=['GET', 'POST'])
def report_page():
    result = None
    error = None
    selected_date = None
    if request.method == 'POST':
        selected_date = request.form['selected_date']
        result, error = main.Main().daily_summary(selected_date)
    return render_template('report.html', result=result, error=error, selected_date=selected_date)

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

def close_resources():
    main.Main().close_connections()

atexit.register(close_resources)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


# pip freeze > requirements.txt