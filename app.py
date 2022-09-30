import json
from flask import Flask, request, jsonify, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS, cross_origin
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
CORS(app)


# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://otqbfelxtngfmd:3a50b35815cb71cd91d127413ca94f3e0ae99743112793216ee6b31f82b355d0@ec2-34-194-40-194.compute-1.amazonaws.com:5432/d518o1rp7o1js8"

db = SQLAlchemy(app)
ma = Marshmallow(app)

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    gallery_image = db.Column(db.String, unique=True)

    def __init__(self, gallery_image):
        self.gallery_image = gallery_image

class GalleryImageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'gallery_image')
    
gallery_image_schema = GalleryImageSchema()
multi_gallery_image_schema = GalleryImageSchema(many=True)

@app.route('/gallery_image/add', methods=["POST"])
def add_gallery_image():
    if request.content_type != 'application/json':
        return jsonify('Error, Send the Data as Json')

    post_data = request.get_json()
    gallery_image = post_data.get('gallery_image')

    if gallery_image == None:
        return jsonify("You must supply a url for this image!")

    new_record = GalleryImage(gallery_image)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(gallery_image_schema.dump(new_record))

@app.route('/gallery_images', methods=['GET'])
def get_all_gallery_images():
    all_records = db.session.query(GalleryImage).all()
    return jsonify(multi_gallery_image_schema.dump(all_records))

@app.route('/gallery_image/<id>', methods=['GET'])
def get_a_gallery_image(id):
    one_record = db.session.query(GalleryImage).filter(GalleryImage.id == id).first()
    return jsonify(gallery_image_schema.dump(one_record))

@app.route("/gallery_image/delete/<id>", methods=["DELETE"])
def delete_id(id):
    gallery_image = GalleryImage.query.get(id)
    db.session.delete(gallery_image)
    db.session.commit()

    return jsonify('successful deletion')

# email functionality

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    print(e)
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.route("/send_email", methods=['OPTIONS','POST'])
@cross_origin(["https://whiteknucklereact.vercel.app"])
def send_email():
    if request.method == 'OPTIONS': 
        return build_preflight_response()
    elif request.method == 'POST':
        if request.content_type != 'application/json':

            return jsonify('Error, Send the Data as Json')

        post_data = request.get_json()
        name = post_data.get('name')
        email = post_data.get('email')
        message = post_data.get('message')

        if name == None or name == "" or email == None or email == "" or message == None or message == "":
            return json.dumps(str("Please provide a name, email and message to send email!")), 400

        sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email("whiteknucklemr@gmail.com")
        to_email = To("whiteknucklemr@gmail.com")
        subject = f'Email from Wk Website {email}' 
        content = Content("text/plain", f'{message} \n {email}')
        mail = Mail(from_email, to_email, subject, content)
        response = sg.send(message=mail)
        response = build_actual_response(response)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return response

def build_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "Content-Type")
    response.headers.add('Access-Control-Allow-Methods', "POST, OPTIONS, GET, DELETE")
    response.headers.add('Content-Type', "application/json")
    return response

def build_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Content-Type', "application/json")
    return response

if __name__ == "__main__":
    app.run(debug=True)