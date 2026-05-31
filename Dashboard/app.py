from flask import Flask, render_template, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
import bcrypt

from models import db, Database, Driver, DrowsinessImage
from routes.api import api


app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db.init_app(app)
app.register_blueprint(api, url_prefix="/api")


class SignUpForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()],
        render_kw={"placeholder": "Name", "class": "kt-input"}
    )
    email = StringField("Email", validators=[DataRequired(), Email()],
        render_kw={"placeholder": "email@email.com", "class": "kt-input"}
    )
    password = PasswordField("Password", validators=[DataRequired()],
        render_kw={"placeholder": "Enter Password", "class": "kt-input"}
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
        render_kw={"placeholder": "Re-enter Password", "class": "kt-input"}
    )
    accept_terms = BooleanField(
        "I accept Terms & Conditions",
        validators=[DataRequired()],
        render_kw={"class": "kt-checkbox kt-checkbox-sm"}
    )
    submit = SubmitField("Sign up", render_kw={"class": "kt-btn kt-btn-primary flex grow"})


    def validate_email(self, field):
        user = Database.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError("Email already registered. Please login.")


class SignInForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()],
        render_kw={"placeholder": "email@email.com", "class": "kt-input"}
    )
    password = PasswordField("Password", validators=[DataRequired()],
        render_kw={"placeholder": "Enter Password", "class": "kt-input"}
    )
    submit = SubmitField("Sign in", render_kw={"class": "kt-btn kt-btn-primary flex grow"})


with app.app_context():
    db.create_all()



@app.route("/")
def main():
    if session.get("email"):
        user = Database.query.filter_by(email=session["email"]).first()
        all_images = DrowsinessImage.query.all()
        return render_template("index.html", user=user, data = all_images)
    return redirect("sign-in")



@app.route("/sign-up", methods=["GET", "POST"])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        hashed_pw = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = Database(username=form.username.data, email=form.email.data, password=hashed_pw)

        db.session.add(user)
        db.session.commit()

        return redirect("/sign-in")

    return render_template("authentication/classic/sign-up/index.html", form=form)



@app.route("/sign-in", methods=["GET", "POST"])
def signin():
    if session.get("email"):
        return redirect("/")

    form = SignInForm()

    if request.method == "POST":
        user = Database.query.filter_by(email=form.email.data).first()

        if user and user.checkpw(form.password.data):
            session["email"] = user.email
            return redirect("/")

    return render_template("authentication/classic/sign-in/index.html", form=form)



@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect("/sign-in")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8001)
