from django.contrib.auth.signals import user_logged_in, user_logged_out,  user_login_failed
from django.dispatch import receiver
import logging

@receiver(user_logged_in)
def sig_user_logged_in(sender, user, request, **kwargs):
    logger = logging.getLogger('essarch.auth')
    logger.info("User %s successfully logged in from host: %s" % (user, request.META['REMOTE_ADDR']))

@receiver(user_logged_out)
def sig_user_logged_out(sender, user, request, **kwargs):
    logger = logging.getLogger('essarch.auth')
    logger.info("User %s successfully logged out from host: %s" % (user, request.META['REMOTE_ADDR']))
    
@receiver(user_login_failed)
def sig_user_login_failed(sender, credentials, **kwargs):
    logger = logging.getLogger('essarch.auth')
    logger.warning("Authentication failure for user: %s, credentials: %s" % (credentials['username'],repr(credentials)))