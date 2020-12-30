import os

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, session, url_for)

try:
  from lxml import etree
  print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")
import hashlib
import re
import time
from functools import wraps
from xml.etree import ElementTree
from xml.dom import minidom

from flask import send_file
from flask_uploads import (TEXT, UploadSet, configure_uploads,
                           patch_request_class)
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from werkzeug.utils import cached_property, secure_filename
from wtforms import SubmitField

#flask_uploads.py
# def extension(filename):
#     ext = os.path.splitext(filename)[1]
#     if ext == '':
#         ext = os.path.splitext(filename)[0]
#     if ext.startswith('.'):
#         # os.path.splitext retains . separator
#         ext = ext[1:]
#     return ext


app = Flask(__name__,static_url_path='',static_folder='static')
app.config['UPLOADED_FILE_DEST'] = os.getcwd()+"/upload"
app.config['UPLOADED_FILE_ALLOW'] = TEXT
app.config['SECRET_KEY'] = 'gift2edxfeifeicomtw'


texts = UploadSet('FILE',TEXT)
configure_uploads(app, texts)
patch_request_class(app)


class UploadForm(FlaskForm):
    text = FileField(label='上傳GIFT題目',validators=[
        FileAllowed(texts, "只允許上傳txt檔"), 
        FileRequired("上傳檔案未選擇")])
    submit = SubmitField(label='進行轉換')

#@app.route('/about')
def about():
    return render_template('items/about.html')

@app.route('/download')
def downloadFile():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "./output/output.xml"
    return send_file(path, as_attachment=True)


@app.route('/', methods=['GET', 'POST'])
def index(edx2=None,moodle=None,arr=None,output=None,totalStr=None):
	form = UploadForm()
	#if request.method == "POST" and 'file' in request.files:
	if form.validate_on_submit():
		#filename = texts.save(request.files['file'])
		name = hashlib.md5(('gift2edx' + str(time.time())).encode('UTF-8')).hexdigest()[:15]
		filename = texts.save(form.text.data, name=name+'.')
		file_url = texts.url(filename)
		edx2,moodle,arr,totalStr,output,blank = gift2edx(texts.path(filename))
		p="<problem>"
		p2="</problem>"
		return render_template('items/index.html', **locals())
	else:
		return render_template('items/index.html', **locals())


def gift2edx(file):
	# 空白檔案
	if os.stat(file).st_size == 0:
		edx2= None
		moodle= None
		arr= None
		totalStr = None
		output = False
		blank = True 
		return edx2,moodle,arr,totalStr,output,blank

	f = open(file,'r', encoding="utf-8")
	lines = f.readlines()



	#Exception generate txt
	def show(myList):
		for x in range(len(myList)):
			print(myList[x],end="")

	for x in range(len(lines)):
		if len(lines[x])==1:
			lines[x] = lines[x].replace("\n","")
	lines = [e for e in lines if e]
	#show(lines)


	arr = list()#Questions that do not conform to the format
	num = list()#Delete the number that does not conform to the format
	x = 0
	#Picture file exception
	while( x < (len(lines)-1)):
		if((lines[x].find('PLUGINFILE') > -1)|(lines[x].find('img src') > -1)|(lines[x].find(' -> ') > -1)):#If this line finds an image file
			i = x #Record found line i look up//question number
			while((lines[i].find('question:')==-1)):
				i = i-1
			
			while((lines[i].find('}')==-1)):
				arr.append(lines[i])
				num.append(i)
				i = i+1
			arr.append(lines[i])
			num.append(i)
			x = i
		x = x+1
	#show(arr)
	
	'''
	for i,element in enumerate(num):
		print(int(element),lines[element],end="\n")
	'''
	num.reverse()
	for i,element in enumerate(num):
		lines.pop(element)
	#show(arr)


	#對照moodle & edx
	moodle = []
	#moodle.append([])
	x = 0
	index = 0
	
	while( x < (len(lines))):
		if((lines[x].find('::') > -1)):#If this line finds the header
			
			moodle.append([])
			i = x #Record found line i look up //question question number

			while((lines[i].find('question:')==-1)):
				i = i-1

			while((lines[i].find('}')==-1)):
				moodle[index].append(lines[i])
				i = i+1

			moodle[index].append(lines[i])
			index = index + 1
			x = i
		x = x+1
	#for i in range(len(moodle)):
#		for j in range(len(moodle[i])):
	#		print(moodle[i][j])
	
	for x in range(len(lines)):
		#lines[x]=re.sub(':.*.:\Dhtml\D',"",lines[x])
		lines[x]=re.sub('::.*.::',"",lines[x])
		lines[x]=re.sub('\Dhtml\D',"",lines[x])
		lines[x]=lines[x].replace('\=','=')
		lines[x]=lines[x].replace('\:',':')
		lines[x]=lines[x].replace('\{','{')
		lines[x]=lines[x].replace('\}','}')
		lines[x]=lines[x].replace('\#',' #')
		lines[x]=lines[x].replace('\\n','<br/>')
		lines[x]=lines[x].replace('&lt;','<')
		if re.match('//.*',lines[x])!= 'None':
			lines[x] = re.sub('// question.*', '', lines[x])
			lines[x] = re.sub('[$].*','',lines[x])
		if len(lines[x])==1:
			lines[x] = lines[x].replace("\n","")
	lines = [e for e in lines if e]
	'''
	print(len(lines[71]))
	#print(lines[71])
	print(lines[71][0])
	'''
	for x in range(len(lines)):
		if len(lines[x])==1:
			lines[x] = lines[x].replace("\n","")

	#show(lines)#Print out a simplified version

	#Calculate the total number of questions
	total = 0
	for x in range(len(lines)):
		if((lines[x][0] == '<')|(lines[x].find('{') > -1)):
			total= total+1
	print('\n')
	print('Total number of questions: ',total)


	#The following judgment is added to the XML format

	#Title root tag is set<problem>
	root = etree.Element("problem")

	def Multiple_choice_question(q_n,index,element,lines):
		#print (index+1,".it is a Multiple_choice_question",lines[element])
		q_response = etree.SubElement(root, "multiplechoiceresponse") 
		label = etree.SubElement(q_response, "label")
		
		q_group = etree.SubElement(q_response, "choicegroup")
		q_group.set("type","MultipleChoice")
		str1 = lines[element]
		
		#c = element
		
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		#str3 = (".\n"+str3)
		index = index+1
		label.text = str3+("<br/>")
		
		for i in range(1,q_n):
			if(lines[element + i][1] == '='):
				choice_T = etree.SubElement(q_group,"choice")
				choice_T.set("correct","true")
				str1 = lines[element + i]
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
				choice_T.text = str1[2:len(str1)]
			else:
				if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
						lines[element] = re.sub('[*]','',lines[element])
						break
				choice_F = etree.SubElement(q_group,"choice")
				choice_F.set("correct","false")
				str2 = lines[element + i]
				str2 = re.sub('[%][-][0-9.]*[%]','',str2)
				str2 = re.sub('[~]','',str2)
				str2 = str2.replace("<p>","")
				str2 = str2.replace("</p>","")
				choice_F.text = str2[1:len(str2)]
				
	def Multiple_selection_question(q_n,index,element,lines):
		#print (index+1,".it is a Multiple_selection_question",lines[element])
		
		q_response = etree.SubElement(root, "choiceresponse") 
		label = etree.SubElement(q_response, "label")
		
		q_group = etree.SubElement(q_response, "checkboxgroup")
		str1 = lines[element]
		
		#c = element
		
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		#str3 = (".\n"+str3)
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		index = index+1
		label.text = str3+("<br/>")

		for i in range(1,q_n):
			if(lines[element + i][3] != '-'):
				if(lines[element + i][2] == '%'):
					choice_T = etree.SubElement(q_group,"choice")
					choice_T.set("correct","true")
					str1 = lines[element + i]
					str1 = str1.replace("<p>","")
					str1 = str1.replace("</p>","")
					str1 = re.sub('[~][%][0-9.]*[%]','',str1)
				
					choice_T.text = str1[1:len(str1)]
				else:
					choice_F = etree.SubElement(q_group,"choice")
					choice_F.set("correct","false")
					str2 = lines[element + i]
					str2 = str2.replace("<p>","")
					str2 = str2.replace("</p>","")
					str2 = re.sub('[~][%][-][0-9.]*[%]','',str2)
					str2 = re.sub('[~]','',str2)
					choice_F.text = str2[1:len(str2)]
			else:
				choice_F = etree.SubElement(q_group,"choice")
				choice_F.set("correct","false")
				str2 = lines[element + i]
				str2 = str2.replace("<p>","")
				str2 = str2.replace("</p>","")
				#str2 = str2.replace("^~%\-|0-9][0-9]%","")#^[\-|0-9][0-9]* 
				str2 = re.sub('[~][%][-][0-9.]*[%]','',str2)
				str2 = re.sub('[~]','',str2)
				choice_F.text = str2[1:len(str2)]
				
				
		
	def Short_answer_question(q_n,index,element,lines):
		#print (index+1,".it is a Short_answer_question",lines[element])
		q_response = etree.SubElement(root, "stringresponse") 
		label = etree.SubElement(q_response, "label")
		
		#q_response.set("answer",str)
		
		#q_group.set("answer",str)
		
		textline = etree.SubElement(q_response,"textline")
		textline.set("size","20")
		str1 = lines[element]
		#c = element
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		#str3 = (".\n"+str3)
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		index = index+1
		#str3 = str3.replace('&amp;gt;','>')
		#str3 = str3.replace('&amp;lt;','<')
		label.text = str3+("<br/>")
		#label.text = label.text.replace('&amp;lt;','<')

		for i in range(1,q_n):
			if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
				lines[element] = re.sub('[*]','',lines[element])
			if(lines[element + i][3] == '1')&(q_n == 2):
				str1 = lines[element + i]
				str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
				str1 = str1[1:len(str1)-2]
				q_response.set("answer",str1)
				break
			elif(lines[element + i][3] == '1')&(q_n > 2):
				if i == 1:
					str1 = lines[element + i]
					str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
					str1 = str1[1:len(str1)-2]
					q_response.set("answer",str1)
					#q_group.set("answer",str1)\
				else:
					str1 = lines[element + i]
					if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
						break
					str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
					str1 = str1[1:len(str1)-2]
					#q_response.set("answer",str1)
					q_group = etree.SubElement(q_response, "additional_answer")
					q_group.set("answer",str1)
				
				
		

	def Matching_question(q_n,index,element,lines):
		print (index+1,".it is a Matching_question ,edx doesn't support",lines[element])
		print("")

	def TF_question(i,a,myList):
		#print (i+1,".it is a TF_question",myList[a])
		str1 = myList[a]
		
		q_response = etree.SubElement(root, "multiplechoiceresponse") 
		label = etree.SubElement(q_response, "label")
		q_group = etree.SubElement(q_response, "choicegroup")
		q_group.set("type","MultipleChoice")

		if (str1.find("{TRUE}")!= -1)|str1.find("T")!= -1:
			choice_T = etree.SubElement(q_group,"choice")
			choice_T.set("correct","true")
			choice_T.text = 'True'
			
			choice_F = etree.SubElement(q_group,"choice")
			choice_F.set("correct","false")
			choice_F.text = 'False'
			if (str1.find("{TRUE}")!= -1):
				str1 = str1.replace('{TRUE}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
			else:	
				str1 = str1.replace('{T}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")

		else:
			choice_T = etree.SubElement(q_group,"choice")
			choice_T.set("correct","false")
			choice_T.text = 'True'
			
			choice_F = etree.SubElement(q_group,"choice")
			choice_F.set("correct","true")
			choice_F.text = 'False'
			if (str1.find("{FALSE}")!= -1):
				str1 = str1.replace('{FALSE}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
			else:	
				str1 = str1.replace('{F}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
		i = i+1
		#str1 = (".\n"+ str1)
		label.text = str1+("<br/>")#放題目 需要先做處理
		


	top = len(lines) #list長度
	def collect(a,myList):
		while myList[a][len(myList[a])-2] != '}':
				a = a+1
		return a+1


	b = 0 #Where is the title in lines
	numlist = [0]
	errorlist = [0]#Problems with image files
	errornum = []#Record the order of the wrong questions to match the original moodle questions

	for i in range(total):
		#print('Question number=',i,',start field:',b)#See where the question is located
		if b<top-1:
			b = collect(b,lines) #Return the location of the next question
			numlist.append(b) #Collect the starting position of the question and put it into the list
	#print(numlist)

	'''
	for i,element in enumerate(numlist):
		print(i,element)
	'''





	for index, element in enumerate(numlist):
		
		if element<top:
			if (lines[element][len(lines[element])-2] == '}')|(lines[element][len(lines[element])-1] == '}'):
				TF_question(index,element,lines)
			else:
				count = 0
				count2 = 0
				q_n = 0 #There are several options
				c = element
				while lines[c][0] != '}':
					if (lines[c][1]) == '=':
						count = count + 1
					if (lines[c][2]) == '%':
						count2 = count2 + 1
					else:
						if (lines[c][1]) == '~':
								count2 = count2 + 1
					c = c + 1
					q_n = q_n + 1
				#print("count = ",count,"count2 = ",count2)
				if count == 0:
					Multiple_selection_question(q_n,index,element,lines)
				elif count == 1 & (count2 > 1):
					Multiple_choice_question(q_n,index,element,lines)
				elif count == count2:
					#print (".it is a Short_answer_question")
					Short_answer_question(q_n,index,element,lines)
				elif count == (q_n - 1) :
					Matching_question(q_n,index,element,lines)
		else:
			break
		




	x = etree.tostring(root, encoding='unicode', pretty_print=True)
	#x = x.replace('&lt;','<')
	#x = x.replace('&gt;','>')

	x = x.replace('&amp;lt;','&lt;')
	x = x.replace('&amp;gt;','&gt;')
	#print(x) #全部
	totalStr = x 
	#--------Find\n---------


	#--------*Write file---------

	with open("./output/output.xml", "w", encoding="utf-8") as output_file:
		   output_file.write(x)
	#--------------------

	#--------*Close---------
	f.close()
	output_file.close
	#--------------------


	i = 0
	p = 0
	j = 0#index [j][]
	edx = list()
	edx2 = []


	edx = x.split('\n')
	edx.remove('<problem>')
	edx.remove('</problem>')

	x = 0
	edx2.append([])

	while(x<len(edx)):
		if((edx[x].find('</multiplechoiceresponse>') < 0) & (edx[x].find('</choiceresponse>')< 0)&(edx[x].find('</stringresponse>')<0)):
					edx2[j].append(edx[x].strip())
		else:
			edx2[j].append(edx[x].strip())
			edx2.append([])
			j = j+1
		x = x+1
	edx2.pop()
	'''

			edx2[j].append(edx[x])
		else:
			edx2[j].append(edx[x])
			edx2.append([])
			j = j+1
		x = x+1	
	'''
	for i in range(len(moodle)):
		for j in range(len(moodle[i])):
			moodle[i][j] = moodle[i][j].replace('\n','').strip()
			#lines[x] = lines[x].replace("\n","")
	#show(edx)


	def show1(a):
		for i in range(len(a)):
			for j in range(len(a[i])):
				print(i,j,a[i][j])


	#--------edx Single topic----------
	#print("\n\nedx Single topic\n")
	#show1(edx2)
	#--------moodle Single topic-------
	#print("\n\nmoodle Single topic\n")
	#show1(moodle)
	#--------Questions that do not conform to the format------
	#print("\n\nQuestions that do not conform to the format\n")
	#show(arr)
	'''
	edx2
	moodle


	'''
	output = True
	blank = False
	return edx2,moodle,arr,totalStr,output,blank

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
