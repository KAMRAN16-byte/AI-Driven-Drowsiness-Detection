from flask import Blueprint, request, jsonify
import os, time

from models import db, Driver, DrowsinessImage


api = Blueprint("api", __name__)

UPLOAD_FOLDER = "static/uploads"


@api.route("/upload", methods=["POST"])
def upload():
    driver_name = request.form.get("driver_name")
    file = request.files.get("image")

    if not driver_name or not file:
        return jsonify({"error": "Missing driver_name or image"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    #filename = f"{driver_name}_{int(time.time())}.jpg"
    filename = f"{driver_name}_{int(time.time())}.jpg"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    driver = Driver.query.filter_by(name=driver_name).first()
    if not driver:
        driver = Driver(name=driver_name)
        db.session.add(driver)
        db.session.commit()

    record = DrowsinessImage(
        driver_id=driver.id,
        image_path=f"/static/uploads/{filename}"
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"message": "uploaded"})
