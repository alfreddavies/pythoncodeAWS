from flask import Flask, render_template, request
import boto3
import pymysql
import os

app = Flask(__name__)

bucket_name = os.environ["S3_BUCKET_NAME"]


def get_db_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=3306,
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connect_timeout=10
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

    if not photo or not photo.filename:
        return "Please select a photo", 400

    s3 = boto3.client('s3')

    s3.upload_fileobj(
        photo,
        bucket_name,
        photo.filename
    )

    # The bucket is private, so do not create a public URL.
    photo_url = f"s3://{bucket_name}/{photo.filename}"

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO students
                (name, email, course, photo_url)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (name, email, course, photo_url)
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return "Student Registered Successfully"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
