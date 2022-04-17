import sys

def get_exception_details():
    exc_type, exc_obj, tb = sys.exc_info()
    line_no = tb.tb_lineno
    return 'Exception at line:{},{}:{}'.format(line_no, exc_type, exc_obj)