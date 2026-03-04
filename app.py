from flask import Flask
from auth import auth as auth_blueprint
from main import main as main_blueprint
from database import db, mail
from logging.config import dictConfig
from flask_login import LoginManager
from models import User

# Configure logging settings
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "flask.log",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "fileLogger": {
                "level": "DEBUG",
                "handlers": ["file"],
            }
        },
    }
)

import os

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    # 配置上传文件夹和处理文件夹路径
    app.config['UPLOAD_FOLDER'] = 'C:\\Users\\86151\\Desktop\\water\\upload_images'
    app.config['PROCESSED_FOLDER'] = 'C:\\Users\\86151\\Desktop\\water\\processed_images'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

    # 确保文件夹存在，如果不存在则创建
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # 传入 exist_ok=True 防止文件夹已存在时报错
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

    # 配置应用程序设置
    app.config['SECRET_KEY'] = 'secret-key'
    app.config['STATIC_FOLDER'] = 'static'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///water.db'

    # 配置邮件设置
    app.config['MAIL_SERVER'] = "smtp.qq.com"
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = "597535178@qq.com"
    app.config['MAIL_PASSWORD'] = "fxfclufwyqzhbgaj"
    app.config['MAIL_DEFAULT_SENDER'] = "597535178@qq.com"

    # 注册蓝图
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)

    # 配置LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 初始化数据库和邮件
    db.init_app(app)
    mail.init_app(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app



if __name__ == '__main__':
    # Run the application in debug mode
    app = create_app()
    app.run(debug=True)
