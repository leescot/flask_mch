from flask import Flask, render_template, request, jsonify
from process_report import process_report

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        report = request.form['report']
        try:
            processed_report = process_report(report)
            input_count = len(report)
            output_count = len(processed_report)
            reduced_count = input_count - output_count
            return jsonify({
                'success': True, 
                'result': processed_report,
                'input_count': input_count,
                'output_count': output_count,
                'reduced_count': reduced_count
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)