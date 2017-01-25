from rest_framework.exceptions import APIException


class NoCSVInArchiveFoundError(APIException):
    status_code = 400
    default_detail = 'Not CSV file found in ZIP archive.'
    default_code = 'bad_request'
