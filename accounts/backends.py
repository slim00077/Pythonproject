from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameModelBackend(ModelBackend):
    """Lets users sign in with either their username or their e-mail address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and '@' in username:
            user_model = get_user_model()
            match = user_model._default_manager.filter(email__iexact=username.strip()).first()
            if match is None:
                user_model().set_password(password)  # same timing as a failed lookup
                return None
            username = match.get_username()
        return super().authenticate(request, username=username, password=password, **kwargs)
