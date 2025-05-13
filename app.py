from flask import Flask
from flask_login import LoginManager
from utils.hashing import bcrypt
from controllers.auth_controller import auth_bp
from models.db import get_connection
from models.user_model import User
from extensions import csrf


from models.user_model import get_user_by_email

app = Flask(__name__)
app.secret_key = "your-secret-key-here"
bcrypt.init_app(app)


csrf.init_app(app)


# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    result = conn.run("SELECT * FROM users WHERE id = :id", id=int(user_id))
    conn.close()
    if result:
        return User(*result[0])
    return None

# Blueprintek
app.register_blueprint(auth_bp)

from controllers.user_controller import user_bp

app.register_blueprint(user_bp)

from controllers.calorie_controller import calorie_bp

app.register_blueprint(calorie_bp)

from controllers.recipe_controller import recipe_bp

app.register_blueprint(recipe_bp)

from controllers.subscription_controller import subscription_bp

app.register_blueprint(subscription_bp)

from controllers.home_controller import home_bp
app.register_blueprint(home_bp)




if __name__ == '__main__':
    print(app.url_map)
    app.run(debug=True)
