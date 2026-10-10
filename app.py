
from flask import Flask, render_template, request
import boto3
import pymysql
import os

app = Flask(__name__)

bucket_name = os.environ.get("S3_BUCKET")


def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        connect_timeout=10,
        read_timeout=10,
        write_timeout=10,
        autocommit=False
    )


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    course = request.form['course']
    photo = request.files['photo']

    if not bucket_name:
        return "S3 bucket configuration is missing.", 500

    if not photo or not photo.filename:
        return "Please select a photo.", 400

    s3 = boto3.client('s3')

    s3.upload_fileobj(
        photo,
        bucket_name,
        photo.filename
    )

    photo_url = (
        f"https://{bucket_name}.s3.amazonaws.com/"
        f"{photo.filename}"
    )

    db = None

    try:
        db = get_db_connection()

        with db.cursor() as cursor:
            sql = """
            INSERT INTO students
            (name, email, course, photo_url)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (name, email, course, photo_url)
            )

        db.commit()

        return "Student Registered Successfully"

    except Exception:
        if db:
            db.rollback()

        app.logger.exception("Student registration failed")
        return "Registration failed. Please check the application logs.", 500

    finally:
        if db:
            db.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
