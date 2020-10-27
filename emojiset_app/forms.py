# Customize the Register form:
from flask_user.forms import RegisterForm, EditUserProfileForm
from flask_user import UserManager
from wtforms import StringField, validators


class CustomRegisterForm(RegisterForm):
    # Add a country field to the Register form
    first_name = StringField(('First name'), validators=[validators.DataRequired()])
    last_name = StringField(('Last name'), validators=[validators.DataRequired()]) 
    country = StringField(('Country'), validators=[validators.DataRequired()])
    description = StringField(('Who are you?'), validators=[validators.DataRequired()])


# Customize the User profile form:
class CustomUserProfileForm(EditUserProfileForm):
    # Add a country field to the UserProfile form
    country = StringField(('Country'), validators=[validators.DataRequired()])
    description = StringField(('Who are you?'), validators=[validators.DataRequired()])


# Customize Flask-User
#from flask_user import StringField
class CustomUserManager(UserManager):
    def customize(self, app):
        # Configure customized forms
        self.RegisterFormClass = CustomRegisterForm
        self.UserProfileFormClass = CustomUserProfileForm
