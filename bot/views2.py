from django.shortcuts import render, HttpResponse
import speech_recognition as sr
import nltk
import pickle
import json
import MySQLdb
from nltk.stem import WordNetLemmatizer 
# Create your views here.

def home(request):
    return render(request, 'home.html', {'data': 'Naveen'})

def get_sql(request):
    sample_text = request.GET['post_id']
    with open('static/table_attributes.json') as f:
        table_attributes = json.load(f)
    with open('static/mapping.json') as f:
        mapping = json.load(f)
    # print(table_attributes) 
    with open('static/tables_pk.json') as f:
        tables_pk = json.load(f)
    # print(tables_pk)
    tables= pickle.load( open( "static/tables.p", "rb" ) )
    # print(tables)
    tables_relation= pickle.load( open( "static/tables_relation.p", "rb" ) )
    # print(tables_relation)

    result=""
    # def mysqlconnect(sql): 
    #     try: 
    #         db_connection= MySQLdb.connect("localhost","root","","smart_bot") 
    #     except: 
    #         print("Can't connect to database") 
    #         return 0
    #     print("Connected")  
    #     cursor=db_connection.cursor() 
    #     cursor.execute(sql) 
    #     m = cursor.fetchall() 
    #     print('---------------------')
    #     for row in m:
    #         result+=row+"<br>" 
    #     db_connection.close() 



    def isWhere(pos):
        for i in range(len(pos)):
            if(pos[i][1]=='WP$' or pos[i][1]=='WRB'):
                return i
        return -1

    def getAttributes(second_part):
        gr=r"Chunk1: {<CC>?(<NN.?><VB.?>(<JJ.?>*|<IN>)*(<NN.?>|<CD>))*}"

        chunkParser=nltk.RegexpParser(gr)
        chunked=chunkParser.parse(second_part)
        chunked=str(chunked)

        chunked=chunked[3:len(chunked)-1]
        chunked=chunked.split("\n")
        l=[]
        ll=[]
        dic={}

        for line in chunked:
            temp=line[3:len(line)-1].split(" ")
            for j in range(len(temp)):
                l.append(temp[j].split(",")[0])

            ll.append(l[1:])
            l=[]

        #print(chunked)
        #print(ll)
        return ll
        
    def findTable(match,attr_list):
        best_match_list=[]
        for i in tables:
            if i.find(match)!=-1:
                q=[]
                diff=len(i)-len(match)   
                q.append(i)
                q.append(diff)
                best_match_list.append(q)
        best_match_list.sort(key = lambda x: x[1])
        # print(best_match_list)
        p=""
        map_schema={}
        # print(attr_list)
        for i in best_match_list:
            count=0
            for j in attr_list:
                for k in j:
                    if(k.find("/N")!=-1):
                        p=k.split("/")[0]
                        break
                    
                for q in table_attributes[i[0]]:
                    if(q.find(p)!=-1):
                        map_schema[p]=q
                        count+=1
                        # print(q+" "+str(count)+" "+str(j)+" "+str(i))
                if(count==len(attr_list)):
                    return i[0],map_schema
        return '',{}
                
    def condition_args(attr_list,map_schema):
        s1=''
        for i in attr_list:
            flag=False
            vflag=False
            for k in i:
                if(k.find("/N")!=-1 and flag==False):
                    flag=True
                    p=k.split("/")[0]
                    s1+=" "+map_schema[p]
                elif k.find("/CC")!=-1:
                    p=k.split("/")[0]
                    s1+=" "+p.upper()
                elif(k.find("/V")!=-1):
                    vflag=True
                    p=k.split("/")[0]
                    for k in mapping.keys():
                        if p.lower() in mapping[k]:
                            # s1+=" "+k
                            verb=k
                            break
                elif((k.find("/J")!=-1 or k.find("/IN")!=-1)):
                    p=k.split("/")[0]
                    print("verb",verb)
                    for k in mapping.keys():
                        if p.lower() in mapping[k]:
                            print("k",k)
                            if vflag==True:
                                # s1=s1.replace(verb,k)
                                s1+=" "+k
                                print("s1",s1)
                                vflag=False
                            else:
                                s1+=" "+k
                            break
                    # if vflag==True:
                    #     s1.replace(verb,p.lower())
                    # else:
                    #     s1+=" "+p.lower()
                elif(k.find("/N")!=-1 and flag==True):
                    p=k.split("/")[0]
                    if vflag==True:
                        s1+=" "+verb
                    s1+=" '"+p+"'"
                elif(k.find("/CD")!=-1):
                    p=k.split("/")[0]
                    if vflag==True:
                        s1+=" "+verb
                    s1+=" "+p
        return s1
                
                    


        

    lemmatizer = WordNetLemmatizer()
    #sample_text=input("Enter your question: ")
    tokenized=nltk.word_tokenize(sample_text)
    l=[]
    for i in tokenized:
        l.append(lemmatizer.lemmatize(i))
    pos=nltk.pos_tag(l)
    print(pos)
    tname=""
    p=isWhere(pos)
    sql = ''
    if(p!=-1):
        first_part=pos[0:p]
        second_part=pos[p+1:]
        attr_list=getAttributes(second_part)
        print(attr_list)
        tname,map_schema=findTable(first_part[-1][0],attr_list)
        #print(first_part)
        # print("ahdkjd")
        #print(second_part)
        # print(attr_list)
        # print(tname)
        # print(map_schema)
        sql="SELECT * FROM "+tname+" WHERE"
        sql+=condition_args(attr_list,map_schema)+" ;"
        print(sql)
        # mysqlconnect(sql)
        try: 
            db_connection= MySQLdb.connect("localhost","root","","smart_bot") 
        except: 
            print("Can't connect to database") 
            return 0
        print("Connected")  
        cursor=db_connection.cursor() 
        try:
            cursor.execute(sql) 
            m = cursor.fetchall() 
            print('---------------------')
            for row in m:
                result+=str(row)+"<br>" 
        except:
            result = 'Try Again'

        db_connection.close() 


    return HttpResponse('<span> ' + sql +'<br>'+result+ ' </span>')

def record(request):
    re = request.GET['rec']
    if re == 'Start Recording: ':
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print('Speak anything: ')
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                print('\nYou said: {}\n'.format(text))
            except:
                text = 'Sorry could not recognize your file'
    return HttpResponse(text)

def trans(request):
    tr = request.GET['t']
    if tr == 'translate':
        pass 
    return HttpResponse('<span> pppp </span>')