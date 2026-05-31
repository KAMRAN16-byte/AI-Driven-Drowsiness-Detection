from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

class Database(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)

    def checkpw(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    license_no = db.Column(db.String(50))
    images = db.relationship('DrowsinessImage', backref='driver', lazy=True)


class DrowsinessImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    image_path = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
