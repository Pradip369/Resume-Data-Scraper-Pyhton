from django.shortcuts import render

import pdfplumber
import re
import json
from .forms import PdfUploadForm
import fitz
from django.core.files.images import ImageFile
import io
from .models import ImageSaver
from django.http import JsonResponse
import urllib
from django.views.decorators.csrf import csrf_exempt
import requests

def get_edu_add_details(pdf):
    highest_qualification = ''
    college = ''
    year = ''
    address = None
    for page in pdf.pages:
        t = page.extract_text()
        lines = t.split('\n')
        for i,line in enumerate(lines):
            if 'Post Graduates' in line:
                highest_qualification = lines[i+1]
                year= re.search('([0-9]+$)', highest_qualification)
                if year:
                    year = year.group(1)
                    college = lines[i+2]
            if 'Undergraduates' in line and not year:
                highest_qualification = lines[i+1]
                year= re.search('([0-9]+$)', highest_qualification)
                if year:
                    year = year.group(1)
                    college = lines[i+2]
            if 'Address ' in line:
                address = line.replace('Address ','',1)
                # print(address)
    if highest_qualification != '':
        year= re.search('([0-9]+$)', highest_qualification)
        if year:
            year = year.group(1)
        highest_qualification = re.sub('\d', '', highest_qualification)
    return [highest_qualification,college,year,address]

def get_img(request,url,img_no,user_name):
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'}
    response = requests.get(url,headers = headers).content
    file_open = fitz.open(stream = response, filetype="pdf")
    img_inst = file_open.getPageImageList(0)[img_no]
    xref = img_inst[0]
    base_image = file_open.extractImage(xref)
    image_bytes = base_image["image"]
    image = ImageFile(io.BytesIO(image_bytes), name = f'{user_name}.jpg')
    exist = ImageSaver.objects.filter(candidate_image = 'images/' + user_name.replace(' ', '_') + '.jpg')
    if exist.exists():
        for du in exist:
            du.candidate_image.delete()
            du.delete()
    img_inst = ImageSaver.objects.create(candidate_image=image)
    img_url = request.build_absolute_uri(img_inst.candidate_image.url)
    return img_url

import urllib3

@csrf_exempt
def upload_file(request):
    try:
        url = request.GET['file_name']
        http = urllib3.PoolManager()
        temp = io.BytesIO()

        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36', 'Accept': 'text/html,application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        temp.write(http.request("GET", url,headers = headers).data)

        file_name = temp
        pdf = pdfplumber.open(file_name)
        education_details = get_edu_add_details(pdf)
        degree = education_details[0].strip()
        college = education_details[1].strip()
        year_of_pass = education_details[2]
        address = education_details[3]
        page = pdf.pages[0]
        t = page.extract_text()
        lines = t.split('\n')
        t_ex = lines[0].split('-')[1].strip().split(' ')
        exp = f'{t_ex[0]} Year(s)' if t_ex[2] == '0' else f'{t_ex[0]}.{t_ex[2]} Year(s)'
        name = lines[1]
        # print(degree,'-',college,'-',year_of_pass,'-',address,'-',exp,'-',name)
        # print(lines)
        try:
            cur_company = lines[2].split(' at ')[1]
            pat = re.search('([0-9]{2}\.[^.\s]*) Lac',lines[3])
            img_path = get_img(request,url,5,name)
        except IndexError:
            cur_company = lines[3].split(' at ')[1]
            pat = re.search('([0-9]{2}\.[^.\s]*) Lac',lines[4])
            img_path = get_img(request,url,6,name)
        if ' at ' in lines[3]:
            designation = lines[3].split(' at ')[0].split(',')
        else:
            designation = lines[2].split(' at ')[0].split(',')
        cur_location = ''
        if ')' in lines[4]:
            cur_location = lines[4].split(')')[-1].strip()
        else:
            cur_location = lines[3].split(' ')[-1].strip()
        # print(cur_location)
            
        ctc = None
        if pat:
            ctc = f'{pat.group(1)} Lac(s)'
        else:
            img_path = get_img(request,url,4,name)
        # print(cur_company,designation,cur_location,ctc)
        emails = list()
        phone_numbers = list()
        for line in lines:
            if 'Notice Period' in line:
                notice_period = line.replace('Notice Period','',1).strip()
                # print(notice_period,'nc')

            if re.findall('\S+@\S+', line):
                email = re.findall('\S+@\S+', line)
                emails.append(email)

            if re.findall('[0-9]{10} ', line):
                phone_number = re.findall('[0-9]{10}', line)
                phone_numbers.append(phone_number)
        
            # if 'University ' in line:
            #     # print(line)
            #     year_of_pass = line.split(' ')[-1].strip()
        
        # print(year_of_pass)
        # print(emails,phone_numbers)

        primary_mobile_no = phone_numbers[0][0]
        secondary_mobile_no = phone_numbers[0][1] if len(phone_numbers[0]) > 1 else None
        primary_email_id = emails[0][0]
        secondary_email_id = emails[1][0] if len(emails) > 1 else None

        data = dict()
        data['candidate_name'] = name
        data['candidate_profile_picture'] = img_path
        data['primary_mobile_number'] = primary_mobile_no
        data['secondary_mobile_number'] = secondary_mobile_no
        data['primary_email_id'] = primary_email_id
        data['secondary_email_id'] = secondary_email_id
        data['current_location'] = cur_location
        data['address'] = address
        data['current_job_designation'] = (',').join(designation)
        data['total_year_of_experience'] = exp
        data['current_CTC'] = ctc
        data['notice_period'] = notice_period
        data['highest_degree'] = degree
        data['passout_year'] = year_of_pass
        data['university_name'] = college
        data['current_company'] = cur_company  # Extra
        # print(data)
        return JsonResponse({"data" : data}, status=200)
    except Exception as e:
        return JsonResponse({"data":str(e)}, status=400)
    # return JsonResponse({"data":form.errors}, status=400)
    
def get_input(request):
    fm = PdfUploadForm()
    return render(request,'upload_pdf.html',context={'fm' : fm})