from rest_framework.exceptions import APIException


class NoCSVInArchiveFoundError(APIException):
    status_code = 400
    default_detail = 'No CSV file found in ZIP archive.'
    default_code = 'bad_request'


class NotZIPFileError(APIException):
    status_code = 400
    default_detail = 'Uploaded file is not a zip file.'
    default_code = 'bad_request'
