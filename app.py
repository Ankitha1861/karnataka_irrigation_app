from flask import Flask, render_template
from projects.irrigation_projects1.routes import irrigation1_bp
from projects.irrigation_projects2.routes import irrigation2_bp
from projects.irrigation_projects3.routes import irrigation3_bp

app = Flask(__name__)

# Register Blueprints for each team member’s dashboard
app.register_blueprint(irrigation1_bp)
app.register_blueprint(irrigation2_bp)
app.register_blueprint(irrigation3_bp)

# Home page with tabs
@app.route('/')
def home():
    return render_template('home_tabs.html')

if __name__ == '__main__':
    app.run(debug=True)
