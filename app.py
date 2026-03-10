from flask import Flask, render_template
from routes.images import images_bp
from routes.APIImage import api_image_bp
from routes.auth import auth_bp

app = Flask(__name__)

# Register the routes from the images Blueprint
app.register_blueprint(images_bp)
app.register_blueprint(api_image_bp)
app.register_blueprint(auth_bp)

@app.route('/', methods=['GET'])
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
