from flask import Flask, render_template, request, redirect, url_for
import os
from index import d_dtcn  # import your detection function

# Create Flask app using the theme folder for both templates and static files
app = Flask(
    __name__,
    static_folder='site',      # all CSS, JS, images, etc.
    template_folder='site'     # HTML files inside /site
)

# Secret key (optional, but good for forms)
app.config['SECRET_KEY'] = os.urandom(24)

# ------------------ ROUTES ------------------ #

# Home route (loads site/index.html)
@app.route('/', methods=['GET', 'POST'])
def home():
    # If Start button is clicked (form from index.html)
    if request.method == 'POST' and request.form.get('Start') == 'Start':
        try:

            d_dtcn()  # run detection
        except Exception as e:
            print(e.messages)
            return render_template('index.html')
        
    return render_template('index.html')


# Dynamic page loader (about.html, contact.html, etc.)
@app.route('/<page>')
def page(page):
    try:
        return render_template(f'{page}.html')
    except:
        return "404 Page Not Found", 404

@app.route('/home')
def home_page():
    return render_template('team.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
