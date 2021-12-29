import re
from flask_babel import gettext

from seed.models import Deployment

def translate_validation(validation_errors):
    for field, errors in list(validation_errors.items()):
        validation_errors[field] = [gettext(error) for error in errors]
    return validation_errors

# Used to create a valid subdomain name
_subdomain_regex = re.compile('[0-9]*[^A-Za-z0-9\\-]')

def get_internal_name(deployment: Deployment) -> str:
    sub_domain =_subdomain_regex.sub('', (deployment.name or '').lower())
    # Size limit is 63 (Kubernetes follows RFC 1123)
    return (f'd-{deployment.id}-{sub_domain}')[:63]