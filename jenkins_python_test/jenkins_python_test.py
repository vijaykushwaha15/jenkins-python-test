import csv
from werkzeug.security import generate_password_hash ,check_password_hash
from datetime import datetime, timedelta, timezone
import jwt
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import serializers

from config.local import JWT_SECRET_KEY
from apps.discern_admin.models import User
from custom_exception.common_exception import (
    CustomApiException,
)
from messags import Messages
from django.db import connections
from django.db.models import OuterRef, Subquery
from django.contrib.gis.db import models
from django.core.mail import send_mail
from django.template import Context
from django.template.loader import get_template, render_to_string 
from django.core.mail import EmailMultiAlternatives

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        """init method"""
        fields = kwargs.pop("fields", None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


def get_serialized_data(obj, serializer, fields, many= False):
    if fields:
        return serializer(obj, fields=eval(fields), many= many)
    return serializer(obj, many=many)

def generate_access_token(user,company_details):
    present_time = datetime.utcnow()
    exp = present_time + timedelta(minutes=1440)
    token = jwt.encode({'email' :user.email, 'exp' : exp, 'company_details':company_details,\
                        "is_discern_admin": user.is_discern_admin},\
                         key=JWT_SECRET_KEY, algorithm='HS256')
    iat_time = present_time
    return token,iat_time

def generate_refresh_token(user,company_details):
    token = jwt.encode({'email' :user.email, 'exp' : datetime.utcnow() +timedelta(days=60),\
                        'company_details':company_details,\
                        "is_discern_admin": user.is_discern_admin},\
                       key=JWT_SECRET_KEY, algorithm='HS256')
    return token

def check_token_validity(token):
    try:
        decoded_dict = jwt.decode(token,JWT_SECRET_KEY,verify=False)
        user_exist = User.objects.filter(email=decoded_dict.get('email')).first()
        if not user_exist:
            raise Exception
        return decoded_dict, user_exist
    except Exception:
        raise CustomApiException(
                    status_code=401, message=Messages.get('UNAUTHORISED'), location="request"
                )
        
def update_models(instance, update_dict):
    '''Function to update models values'''
    for i, j in update_dict.items():
        setattr(instance, i, j)
    instance.save()

def get_query_response(db,query):
    with connections[db].cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result_set = cursor.fetchall()
        response = []
        for row in result_set:
            data = {}
            for index, item in enumerate(row):
                # create dict with selected columns as dict keys
                if not data.get(row[0], False):
                    data[columns[index]] = row[index]
            response.append(data)

        return response

def get_query_values_response(db,query):
    with connections[db].cursor() as cursor:
        cursor.execute(query)
        result_set = cursor.fetchall()
        response = []
        for row in result_set:
            data = ()
            list_data = list(data)
            for index, item in enumerate(row):
                list_data.append(row[index])
            data = tuple(list_data)
            response.append(data)
        return response


def send_welcome_email(email, url):
    SENDER = "Discern.io Support <support@discern.io>"
    RECIPIENT = email
    SUBJECT = "Welcome to Discern.io!"

    try:
        html_version = 'welcome_email.html' # import html version. Has html content
        html_message = render_to_string(html_version, {'url': url})
        message = EmailMultiAlternatives(SUBJECT, "", SENDER, [RECIPIENT])
        message.attach_alternative(html_message, "text/html") # attach html version
        message.send()
        print(f"Welcome email sent to {email}!")
    except Exception as e:
        print(e)


def send_forget_password_otp(email, url):
    SENDER = "Discern.io Support <support@discern.io>"
    RECIPIENT = email
    SUBJECT = "Your Password Reset Request"

    try:
        html_version = 'reset_email.html' # import html version. Has html content
        html_message = render_to_string(html_version, {'url': url})
        message = EmailMultiAlternatives(SUBJECT, "", SENDER, [RECIPIENT])
        message.attach_alternative(html_message, "text/html") # attach html version
        message.send()
        print(f"Reset Password email sent to {email}!")
    except Exception as e:
        print(e)

def get_universal_filter_string(data,table_alias):
    account_executive = data.get('account_executive')
    deal_size = data.get('deal_size')
    product = data.get('product')
    opportunity_type = data.get('opportunity_type')
    region = data.get('region')
    lead_source = data.get('lead_source')
    sector = data.get('sector')
    channel = data.get('channel')
    industry = data.get('industry')
    territory = data.get('territory')
    manager = data.get('manager')

    filter_string =''
    if product and product!='All':
        filter_string = filter_string + ' and ' +'{}.product = \'{}\''.format(table_alias,product)
    if deal_size and deal_size!='All':
        filter_string = filter_string + ' and ' +'{}.deal_size = \'{}\''.format(table_alias,deal_size)
    if region and region!='All':
        filter_string = filter_string + ' and '+'{}.region = \'{}\''.format(table_alias,region)
    if account_executive and account_executive!='All':
        filter_string = filter_string + ' and '+'{}.owner_id = \'{}\''.format(table_alias,account_executive)
    if opportunity_type and opportunity_type!='All':
        filter_string = filter_string + ' and '+'{}.opportunity_type = \'{}\''.format(table_alias,opportunity_type)
    if industry and industry!='All':
        filter_string = filter_string + ' and '+'{}.industry = \'{}\' '.format(table_alias,industry)
    if lead_source and lead_source!='All':
        filter_string = filter_string + ' and '+'{}.lead_source = \'{}\' '.format(table_alias,lead_source)
    if sector and sector!='All':
        filter_string = filter_string + ' and '+'{}.sector = \'{}\' '.format(table_alias,sector)
    if channel and channel!='All':
        filter_string = filter_string + ' and '+'{}.channel = \'{}\' '.format(table_alias,channel)
    if territory and territory!='All':
        filter_string = filter_string + ' and '+'{}.territory = \'{}\' '.format(table_alias,territory)
    if manager and manager!='All':
        filter_string = filter_string + ' and '+'{}.manager_id = \'{}\' '.format(table_alias,manager)
    return filter_string

class Quarters():
    """Static Quarters"""
    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4

class SQCount(Subquery):
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = models.IntegerField()

class Echo:
    def write(self, value):
        return value

def get_csv_response(base_query,header_row,file_name):
    echo_buffer = Echo()
    final_row = []
    final_row.append(header_row)
    for row in base_query:
        '''Rounding the values in csv'''
        row = (map(lambda x: isinstance(x, str) and x.replace('#', '') or x, row))
        row = tuple(map(lambda x: isinstance(x, float) and round(x, 3) or x, row))
        final_row.append(row)
    csv_writer = csv.writer(echo_buffer)  
    rows = (csv_writer.writerow(row) for row in final_row)
    response = StreamingHttpResponse(rows, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename={}'.format(file_name)
    return response

def get_universal_filters_request(data):
    account_executive = data.get('account_executive')
    deal_size = data.get('deal_size')
    product = data.get('product')
    opportunity_type = data.get('opportunity_type')
    region = data.get('region')
    lead_source = data.get('lead_source')
    sector = data.get('sector')
    channel = data.get('channel')
    frequency = data.get('frequency')
    industry = data.get('industry')
    territory = data.get('territory','All')
    manager = data.get('manager','All')

    return frequency,lead_source,channel,opportunity_type, \
            region, product, deal_size, sector, industry, account_executive, \
            territory, manager

def opportunity_universal_filters(base_query,data):
    ''''getting universal filters'''
    frequency,lead_source,channel,opportunity_type, \
    region, product, deal_size, sector, \
    industry, account_executive, territory, manager = get_universal_filters_request(data)

    if product and product!='All':
        base_query = base_query.filter(product = product)
    if region and region!='All':
        base_query = base_query.filter(region = region)
    if deal_size and deal_size!='All':
        base_query = base_query.filter(deal_size = deal_size)
    if account_executive and account_executive!='All':
        base_query = base_query.filter(owner_id = account_executive)
    if opportunity_type and opportunity_type!='All':
        base_query = base_query.filter(opportunity_type = opportunity_type)
    if industry and industry!='All':
        base_query = base_query.filter(industry = industry)
    if lead_source and lead_source!='All':
        base_query = base_query.filter(lead_source = lead_source)
    if sector and sector!='All':
        base_query = base_query.filter(sector = sector)
    if channel and channel!='All':
        base_query = base_query.filter(channel = channel)
    if territory and territory!='All':
        base_query = base_query.filter(territory = territory)
    if manager and manager!='All':
        base_query = base_query.filter(manager_id = manager)
    return base_query

def calculate_date_range(start_date_format,end_date_format):
    '''function to get filter list from start_date and end_date'''

    months = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    filter_list = []
    if start_date_format.year != end_date_format.year:
        for year in range(start_date_format.year,end_date_format.year):
            if year != start_date_format.year:
                for i in range(1,13):
                        string = ''
                        string = months[i]+'-'+str(year)
                        filter_list.append(string)
            else:
                for i in range(start_date_format.month,13):
                    string = ''
                    string = months[i]+'-'+str(year)
                    filter_list.append(string)

        for i in range(1,(end_date_format.month+1)):
            string = ''
            string = months[i]+'-'+str(end_date_format.year)
            filter_list.append(string)
    else:
        for i in range(start_date_format.month,(end_date_format.month+1)):
            string = ''
            string = months[i]+'-'+str(start_date_format.year)
            filter_list.append(string)
    
    return filter_list
