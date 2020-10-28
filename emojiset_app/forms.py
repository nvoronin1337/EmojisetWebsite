# Customize the Register form:
from flask_user.forms import RegisterForm, EditUserProfileForm
from flask_user import UserManager
from wtforms import StringField, validators, ValidationError
from twarc import Twarc


class CustomRegisterForm(RegisterForm):
    # Add a country field to the Register form
    access_token = StringField(('Acess Token'), validators=[validators.DataRequired()])
    access_token_secret = StringField(('Access Token Secret'), validators=[validators.DataRequired()])
    consumer_key = StringField(('Consumer Key'), validators=[validators.DataRequired()])
    consumer_secret = StringField(('Consumer Secret'), validators=[validators.DataRequired()])

    
    def validate_access_token(form, field):
        a_token = field.data
        a_token_secret = form.access_token_secret.data
        c_key = form.consumer_key.data
        c_secret = form.consumer_secret.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')

    def validate_access_token_secret(form, field):
        a_token = form.access_token.data
        a_token_secret = field.data
        c_key = form.consumer_key.data
        c_secret = form.consumer_secret.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')
    
    def validate_consumer_key(form, field):
        a_token = form.access_token.data
        a_token_secret = form.access_token_secret.data
        c_key = field.data
        c_secret = form.consumer_secret.data   
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')
    
    def validate_consumer_secret(form, field):
        a_token = form.access_token.data
        a_token_secret = form.access_token_secret.data
        c_key = form.consumer_key.data
        c_secret = field.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')


# Customize the User profile form:
class CustomEditUserProfileForm(EditUserProfileForm):
    # Add a country field to the UserProfile form
    first_name = StringField(('First name'))
    last_name = StringField(('Last name'))
    country = StringField(('Country'))
    description = StringField(('Who are you?'))
    access_token = StringField(('Acess Token'), validators=[validators.DataRequired()])
    access_token_secret = StringField(('Access Token Secret'), validators=[validators.DataRequired()])
    consumer_key = StringField(('Consumer Key'), validators=[validators.DataRequired()])
    consumer_secret = StringField(('Consumer Secret'), validators=[validators.DataRequired()])

    def validate_access_token(form, field):
        a_token = field.data
        a_token_secret = form.access_token_secret.data
        c_key = form.consumer_key.data
        c_secret = form.consumer_secret.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')

    def validate_access_token_secret(form, field):
        a_token = form.access_token.data
        a_token_secret = field.data
        c_key = form.consumer_key.data
        c_secret = form.consumer_secret.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')
    
    def validate_consumer_key(form, field):
        a_token = form.access_token.data
        a_token_secret = form.access_token_secret.data
        c_key = field.data
        c_secret = form.consumer_secret.data   
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')
    
    def validate_consumer_secret(form, field):
        a_token = form.access_token.data
        a_token_secret = form.access_token_secret.data
        c_key = form.consumer_key.data
        c_secret = field.data
        try:
            twarc = Twarc(c_key, c_secret, a_token, a_token_secret)
        except RuntimeError:
            raise ValidationError('at least one of the API keys are not valid!')


# Customize Flask-User
#from flask_user import StringField
class CustomUserManager(UserManager):
    def customize(self, app):
        # Configure customized forms
        self.RegisterFormClass = CustomRegisterForm
        self.EditUserProfileFormClass = CustomEditUserProfileForm
