from flask import *

error = Blueprint('error', __name__, template_folder='views')

@error.errorhandler(404)
def page_not_found(error):
	return render_template('page_not_found.html'), 404