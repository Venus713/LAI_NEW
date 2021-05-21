def get_readable_fb_exception_details(e):
    return e.body()['error']['error_user_msg']
