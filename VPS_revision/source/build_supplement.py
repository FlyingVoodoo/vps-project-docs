"""Detailed BPMN collaborations and numbered architecture trajectories."""
from build_diagrams import Diagram,COL
from lxml import etree as E
import math,json
from pathlib import Path

AUDIT=[]
def label(d,id,box,t,size=18):
    d.text(box,t,size)
    x,y,w,h=box
    c=E.SubElement(d.root,'mxCell',id=id,value=t,vertex='1',parent='1',style=f'text;html=0;whiteSpace=wrap;fontSize={size};fontFamily=DejaVu Sans;')
    E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
def pool(d,id,x,w,title,lanes):
    d.box(id,x,100,w,1330,'','external','audit')
    d.d.rectangle((x*2,200,(x+w)*2,290),fill='#e2e8f0',outline=COL['audit'],width=2)
    label(d,id+'label',(x,100,w,45),title,20)
    d.pools[id]=id
    xx=x
    for lid,lw,lt in lanes:
        d.d.line((xx*2,290,xx*2,2860),fill='#cbd5e1',width=2)
        label(d,lid+'label',(xx,150,lw,55),lt,18)
        xx+=lw
def node(d,id,x,y,w,h,t,poolid,kind='box',group='identity',size=20):
    d.box(id,x,y,w,h,t,kind,group,size=size);d.pools[id]=poolid
def event(d,id,x,y,poolid,kind='start',message=False,timer=False,group='identity'):
    node(d,id,x,y,44,44,'',poolid,'end' if kind=='end' else 'event',group)
    c=COL[group]
    if kind=='catch':d.d.ellipse((x*2+7,y*2+7,(x+44)*2-7,(y+44)*2-7),outline=c,width=2)
    cell=d.root.xpath(f'./mxCell[@id="{id}"]')[0]
    if kind=='catch':cell.set('style',cell.get('style')+'shape=doubleEllipse;')
    if message:
        d.d.rectangle(((x+10)*2,(y+14)*2,(x+34)*2,(y+30)*2),outline=c,width=2)
        d.d.line(((x+10)*2,(y+14)*2,(x+22)*2,(y+23)*2,(x+34)*2,(y+14)*2),fill=c,width=2)
        cell.set('value','✉')
    if timer:
        d.d.ellipse(((x+9)*2,(y+9)*2,(x+35)*2,(y+35)*2),outline=c,width=2)
        d.d.line(((x+22)*2,(y+13)*2,(x+22)*2,(y+22)*2,(x+29)*2,(y+26)*2),fill=c,width=2)
        cell.set('value','◷')
def port(d,id,s):
    x,y,w,h=d.nodes[id]
    return {'left':(x,y+h/2),'right':(x+w,y+h/2),'top':(x+w/2,y),'bottom':(x+w/2,y+h)}[s]
def flow(d,a,b,t='',message=False,**kw):
    st=kw.get('start','bottom');en=kw.get('end','top');pts=kw.get('points',[])
    assert (d.pools[a]!=d.pools[b])==message,(d.name,a,b,message)
    d.edge(a,b,t,dashed=message,arrow=not message,**kw)
    d.flows.append({'source':a,'target':b,'message':message,'label':t})
    if message:
        p=port(d,a,st);q=port(d,b,en);prev=pts[-1] if pts else p
        ang=math.atan2(q[1]-prev[1],q[0]-prev[0]);c=COL[kw.get('color','audit')]
        for da in [-.4,.4]:d.d.line((q[0]*2,q[1]*2,(q[0]-12*math.cos(ang+da))*2,(q[1]-12*math.sin(ang+da))*2),fill=c,width=3)
        d.d.ellipse((p[0]*2-5,p[1]*2-5,p[0]*2+5,p[1]*2+5),fill='white',outline=c,width=2)
        cell=d.root.findall('mxCell')[-1];cell.set('style',cell.get('style')+'startArrow=oval;startFill=0;endArrow=open;endFill=0;')
def new(name,title):
    d=Diagram(name,title,1100,1520);d.pools={};d.flows=[];return d
def finish(d):
    d.note(1445,'Сплошная стрелка — поток управления внутри пула. Пунктир с кружком и открытой стрелкой — сообщение между пулами. Ромб X — исключающий шлюз.');d.save()
    AUDIT.append({'diagram':d.name,'pools':d.pools,'flows':d.flows})

def registration():
    d=new('06_bpmn_registration','BPMN • регистрация: участники и транзакция')
    pool(d,'client',25,280,'Клиент',[('clane',280,'Пользователь')])
    pool(d,'service',330,745,'Система аренды VPS/VDS',[('api',365,'Identity / API'),('tx',380,'Транзакционный слой')])
    event(d,'cs',145,230,'client');node(d,'form',55,320,220,90,'Заполнить и\nотправить форму','client')
    event(d,'cw',145,1210,'client','catch',True);event(d,'ce',145,1340,'client','end')
    label(d,'cwait',(40,1130,250,65),'Получить профиль\nили причину отказа',18)
    event(d,'ss',490,340,'service',message=True)
    node(d,'validate',380,445,270,90,'Проверить формат\nи политику пароля','service')
    node(d,'valid',465,600,100,80,'X','service','diamond',size=24)
    label(d,'validlabel',(350,548,320,45),'Данные корректны?',18)
    node(d,'email',380,755,270,90,'Проверить\nуникальность email','service')
    node(d,'unique',465,915,100,80,'X','service','diamond',size=24)
    label(d,'ulabel',(345,860,330,45),'Email свободен?',18)
    node(d,'create',750,1010,270,110,'Создать пользователя,\nсчёт и аудит; commit','service',group='infra')
    node(d,'error',750,680,270,90,'Вернуть ошибку;\nоткатить при конфликте','service',group='support')
    event(d,'errend',862,845,'service','end',group='support')
    event(d,'txerr',998,1042,'service','catch',group='support');label(d,'txerrlabel',(750,1130,315,50),'Конфликт UNIQUE / сбой',17)
    d.text((998,1042,44,44),'ϟ',25,COL['support'])
    d.root.xpath('./mxCell[@id="txerr"]')[0].set('value','ϟ')
    node(d,'result',380,1170,270,90,'Вернуть созданный\nпрофиль и счёт','service')
    event(d,'se',490,1340,'service','end')
    for a,b in [('cs','form'),('form','cw'),('cw','ce'),('ss','validate'),('validate','valid'),('email','unique'),('error','errend'),('result','se')]:flow(d,a,b,color='identity')
    flow(d,'form','ss','Форма',True,start='right',end='left',points=[(317,365),(317,362)],label_at=(242,280,150,40),color='identity')
    flow(d,'valid','email','Да',label_at=(520,700,60,35),color='identity')
    flow(d,'valid','error','Нет',start='right',end='top',points=[(885,640)],label_at=(645,601,100,35),color='support')
    flow(d,'unique','create','Да',start='right',end='top',points=[(885,955)],label_at=(640,916,100,35),color='infra')
    flow(d,'unique','error','Нет',start='right',end='left',points=[(715,955),(715,725)],label_at=(600,849,100,35),color='support')
    flow(d,'create','result',start='bottom',end='right',points=[(885,1215)],color='infra')
    flow(d,'txerr','error',start='right',end='right',points=[(1055,1064),(1055,725)],color='support')
    flow(d,'result','cw','Профиль',True,start='left',end='right',points=[(318,1215),(318,1232)],label_at=(218,1260,160,40),color='identity')
    flow(d,'error','cw','Причина отказа',True,start='left',end='left',points=[(315,725),(315,1100),(40,1100),(40,1232)],label_at=(35,1030,260,45),color='support')
    finish(d)

def support():
    d=new('07_bpmn_support','BPMN • поддержка: назначение, ответ и повтор')
    pool(d,'client',25,280,'Клиент',[('clane',280,'Пользователь')])
    pool(d,'service',330,745,'Система аренды VPS/VDS',[('api',365,'Support / API'),('agent',380,'Специалист поддержки')])
    event(d,'cs',145,230,'client');node(d,'send',55,320,220,90,'Выбрать VPS;\nотправить обращение','client',group='support')
    event(d,'answer',145,880,'client','catch',True,group='support')
    node(d,'wait',110,485,110,85,'','client','diamond','support',size=24)
    # BPMN event-based gateway: double circle enclosing a pentagon.
    for radius in [24,20]:d.d.ellipse(((165-radius)*2,(527-radius)*2,(165+radius)*2,(527+radius)*2),outline=COL['support'],width=2)
    vertices=[(165+12*math.cos(-math.pi/2+i*2*math.pi/5),527+12*math.sin(-math.pi/2+i*2*math.pi/5)) for i in range(5)]
    d.d.polygon([(x*2,y*2) for x,y in vertices],outline=COL['support'],width=2)
    for id,shape,x,y,w,h in [('waitcircle','doubleEllipse',141,503,48,48),('waitpentagon','pentagon',153,515,24,24)]:
        cell=E.SubElement(d.root,'mxCell',id=id,vertex='1',parent='1',style=f'shape={shape};fillColor=none;strokeColor={COL["support"]};')
        E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
    node(d,'decisiontask',55,1000,220,110,'Оценить ответ;\nотправить решение','client',group='support')
    node(d,'accept',110,1195,110,85,'X','client','diamond','support',size=24);label(d,'alabel',(35,1140,260,42),'Ответ принят?',18)
    event(d,'ce',145,1340,'client','end',group='support')
    event(d,'ss',490,340,'service',message=True,group='support')
    node(d,'check',380,450,270,90,'Проверить владельца\nи данные обращения','service',group='support')
    node(d,'own',465,590,100,80,'X','service','diamond','support',size=24);label(d,'ownlabel',(350,546,330,38),'Доступ разрешён?',18)
    node(d,'reject',750,450,270,90,'Вернуть отказ;\nтикет не создавать','service',group='support');event(d,'re',862,590,'service','end',group='support')
    node(d,'open',380,745,270,90,'Создать тикет OPEN','service',group='support')
    node(d,'assign',750,745,270,90,'Назначить исполнителя;\nIN_PROGRESS','service',group='support')
    node(d,'solve',750,930,270,90,'Провести диагностику;\nответ; RESOLVED','service',group='support')
    event(d,'decision',490,1070,'service','catch',True,group='support')
    node(d,'choice',465,1175,100,80,'X','service','diamond','support',size=24)
    label(d,'choice_label',(350,1130,330,40),'Решение клиента?',18)
    node(d,'close',750,1285,270,75,'CLOSED','service',group='support');event(d,'se',862,1375,'service','end',group='support')
    node(d,'reopen',380,1285,270,75,'Тот же тикет → OPEN','service',group='support')
    for a,b in [('cs','send'),('send','wait'),('answer','decisiontask'),('decisiontask','accept'),('ss','check'),('check','own'),('reject','re'),('open','assign'),('assign','solve'),('decision','choice'),('close','se')]:
        kw={'start':'right','end':'left'} if (a,b)==('open','assign') else {}
        flow(d,a,b,color='support',**kw)
    flow(d,'send','ss','Обращение',True,start='right',end='left',points=[(318,365),(318,362)],label_at=(235,280,190,42),color='support')
    flow(d,'own','open','Да',label_at=(520,687,65,35),color='support')
    flow(d,'own','reject','Нет',start='right',end='left',points=[(715,630),(715,495)],label_at=(600,580,90,35),color='support')
    # Refusal is a separate client branch: it ends without entering the resolution loop.
    event(d,'refusal',60,625,'client','catch',True,group='support');event(d,'refend',60,745,'client','end',group='support')
    flow(d,'wait','refusal',start='left',end='top',points=[(82,527)],color='support')
    flow(d,'wait','answer',start='right',end='top',points=[(285,527),(285,850),(167,850)],color='support')
    flow(d,'reject','refusal','Отказ',True,start='left',end='right',points=[(715,495),(715,700),(315,700),(315,647)],label_at=(130,680,160,35),color='support');flow(d,'refusal','refend',color='support')
    # Event-based wait separates refusal and a substantive answer; only one arrives.
    # The two catch paths model alternative incoming messages to this participant.
    flow(d,'solve','answer','Ответ',True,start='left',end='right',points=[(710,975),(710,902)],label_at=(360,908,200,40),color='support')
    flow(d,'accept','ce','Да',label_at=(175,1290,65,35),color='support')
    flow(d,'accept','answer','Нет',start='right',end='right',points=[(285,1237),(285,902)],label_at=(220,1300,65,35),color='support')
    flow(d,'decisiontask','decision','Принять / повторить',True,start='right',end='left',points=[(315,1055),(315,1092)],label_at=(215,1115,225,45),color='support')
    flow(d,'choice','close','Принять',start='right',end='left',points=[(710,1215),(710,1322)],label_at=(585,1240,160,35),color='support')
    flow(d,'choice','reopen','Повторить',label_at=(350,1245,180,35),color='support')
    flow(d,'reopen','assign',start='right',end='left',points=[(715,1322),(715,790)],color='support')
    finish(d)

def deletion():
    d=new('08_bpmn_delete','BPMN • удаление VPS: команда и подтверждение')
    pool(d,'client',25,230,'Клиент',[('clane',230,'Пользователь')])
    pool(d,'service',280,510,'Система аренды VPS/VDS',[('api',250,'API / Provisioning'),('worker',260,'Worker')])
    pool(d,'hyper',815,260,'Гипервизор',[('hlane',260,'Внешняя система')])
    event(d,'cs',115,230,'client');node(d,'send',45,330,190,90,'Запросить\nудаление VPS','client',group='vps')
    event(d,'cw',115,1255,'client','catch',True,group='vps');event(d,'ce',115,1370,'client','end',group='vps')
    event(d,'ss',383,350,'service',message=True,group='vps')
    node(d,'mark',305,495,200,110,'Проверить доступ;\nDELETING; commit','service',group='vps',size=19)
    node(d,'remove',555,495,210,110,'Удалить / сверить\nВМ по vm_key','service',group='vps',size=19)
    event(d,'hs',920,520,'hyper',message=True,group='ext')
    node(d,'actual',840,700,210,100,'Удалить ВМ;\nвернуть состояние','hyper',group='ext',size=19);event(d,'he',920,885,'hyper','end',group='ext')
    node(d,'absent',610,730,100,80,'X','service','diamond','vps',size=24);label(d,'ablabel',(540,667,240,50),'ВМ отсутствует?',18)
    event(d,'timer',638,970,'service','catch',timer=True,group='vps');label(d,'timerlabel',(540,1020,240,55),'Тайм-аут / ВМ есть:\nсохранить резерв',17)
    node(d,'finish',305,1100,200,110,'DELETED; снять\nрезерв; аудит; commit','service',group='vps',size=19)
    node(d,'return',305,1260,200,80,'Вернуть результат','service',group='vps',size=19);event(d,'se',383,1370,'service','end',group='vps')
    for a,b in [('cs','send'),('send','cw'),('cw','ce'),('ss','mark'),('actual','he'),('finish','return'),('return','se')]:flow(d,a,b,color='vps')
    flow(d,'send','ss','Команда',True,start='right',end='left',points=[(267,375),(267,372)],label_at=(215,290,150,40),color='vps')
    flow(d,'mark','remove',start='right',end='left',color='vps')
    flow(d,'remove','hs','delete / inspect',True,start='right',end='left',points=[(802,550),(802,542)],label_at=(760,440,310,45),color='ext')
    flow(d,'hs','actual',color='ext')
    flow(d,'actual','remove','Фактическое состояние',True,start='left',end='right',points=[(802,750),(802,550)],label_at=(775,820,300,50),color='ext')
    # API call task completion includes a response or timeout; the XOR tests it.
    flow(d,'remove','absent',color='vps')
    flow(d,'absent','finish','Да',start='left',end='top',points=[(520,770),(520,1060),(405,1060)],label_at=(440,908,65,35),color='vps')
    flow(d,'absent','timer','Нет / неизвестно',label_at=(548,860,235,45),color='support')
    flow(d,'timer','remove',start='right',end='right',points=[(780,992),(780,550)],label_at=(540,1130,240,70),color='support')
    flow(d,'return','cw','Итог удаления',True,start='left',end='right',points=[(267,1300),(267,1277)],label_at=(35,1185,220,45),color='vps')
    label(d,'rejectnote',(35,665,215,180),'Отказ доступа и повтор уже выполненной команды возвращаются до запуска Worker. Основная ветвь показана для разрешённой команды.',17)
    finish(d)

def trajectory(name,title,nodes,edges,notes):
    d=Diagram(name,title,1100,1400)
    for id,x,y,w,h,t,g,k in nodes:
        d.box(id,x,y,w,h,t,k,g,size=21)
        if k in ('filled','box'):
            for yy in [y+13,y+33]:d.d.rectangle(((x-5)*2,yy*2,(x+12)*2,(yy+12)*2),fill='white',outline=COL[g],width=2)
            cell=d.root.xpath(f'./mxCell[@id="{id}"]')[0];cell.set('style',cell.get('style')+'shape=component;')
    for a,b,number,st,en,pts,la in edges:d.edge(a,b,str(number),pts,start=st,end=en,label_at=la,color='audit')
    d.note(1300,notes);d.save()

def architecture_paths():
    trajectory('16_path_infrastructure','Траектория A2: публикация версии тарифа',[
        ('a',30,100,300,90,'Администратор','identity','person'),('ui',390,100,340,90,'Рабочая панель','identity','filled'),('s',390,340,340,90,'Security','identity','box'),('i',390,580,340,100,'Infrastructure','infra','filled'),('u',390,840,340,100,'Unit of Work','audit','filled'),('db',30,1100,300,130,'D2 Ноды / тарифы','infra','db'),('audit',770,840,300,100,'Audit','audit','box'),('d6',770,1100,300,130,'D6 Аудит','audit','db')], [
        ('a','ui',1,'right','left',[],(310,200,90,40)),('ui','s',2,'bottom','top',[],(560,245,90,40)),('s','i',3,'bottom','top',[],(560,485,90,40)),('i','u',4,'bottom','top',[],(560,735,90,40)),('u','db',5,'left','top',[(180,890)],(105,965,90,40)),('u','audit',6,'right','left',[],(715,805,90,40)),('audit','d6',7,'bottom','top',[],(925,990,90,40)),('u','ui',8,'left','left',[(350,890),(350,145)],(270,420,90,40))],
        'Номера стрелок соответствуют пошаговой таблице. Шаги 4–7 — одна транзакция; ответ 8 отправляется после commit.')
    trajectory('17_path_rent','Траектория A3: заказ и создание VPS',[
        ('c',30,100,280,90,'Клиент','identity','person'),('api',390,100,340,90,'Web UI / API','identity','filled'),('sec',770,100,300,90,'Security','identity','box'),('p',390,360,340,100,'Provisioning','vps','filled'),('b',30,620,280,100,'Billing','money','box'),('u',390,620,340,100,'Unit of Work','audit','filled'),('db',770,620,300,130,'PostgreSQL\nD1–D4; D6','infra','db'),('w',390,930,340,100,'Worker','vps','filled'),('h',30,1120,280,100,'Hypervisor Adapter','ext','box'),('hv',770,1120,300,100,'Гипервизор','ext','external')], [
        ('c','api',1,'right','left',[],(280,210,90,40)),('api','sec',2,'right','left',[],(715,210,90,40)),('api','p',3,'bottom','top',[],(560,260,90,40)),('p','b',4,'left','top',[(170,410)],(120,490,90,40)),('p','u',5,'bottom','top',[],(560,515,90,40)),('u','db',6,'right','left',[],(715,740,90,40)),('p','api',7,'left','left',[(350,410),(350,145)],(270,300,90,40)),('w','db',8,'right','bottom',[(920,980)],(870,850,90,40)),('w','h',9,'left','top',[(170,980)],(120,1040,90,40)),('h','hv',10,'right','left',[],(470,1070,90,40)),('hv','h',11,'bottom','bottom',[(920,1260),(170,1260)],(470,1220,90,40)),('h','w',12,'top','left',[(170,1060),(350,1060),(350,980)],(260,1040,90,40)),('w','db',13,'top','bottom',[(560,840),(850,840)],(620,800,90,40)),('api','db',14,'right','top',[(1090,145),(1090,500),(920,500)],(965,425,90,40))],
        'API отвечает о принятии заказа до завершения Worker. Шаг 14 — последующее чтение статуса, а не обещание синхронного запуска.')
    trajectory('18_path_payment','Траектория A4: пополнение лицевого счёта',[
        ('c',30,100,300,90,'Клиент','identity','person'),('api',390,100,340,90,'Web UI / API','identity','filled'),('pa',390,350,340,100,'Payment Adapter','money','filled'),('pr',770,350,300,100,'Платёжный провайдер','ext','external'),('b',390,650,340,100,'Billing','money','box'),('u',390,900,340,100,'Unit of Work / Audit','audit','filled'),('db',390,1140,340,130,'D1 Счёт; D4 Проводки;\nD6 Аудит','infra','db')],[
        ('c','api',1,'right_top','left_top',[],(310,210,90,40)),('api','pa',2,'bottom','top',[],(565,260,90,40)),('pa','pr',3,'right_top','left_top',[],(715,285,90,40)),('pr','pa',4,'left_bottom','right_bottom',[],(715,470,90,40)),('pa','api',5,'left','left',[(350,400),(350,145)],(260,300,90,40)),('api','c',6,'left_bottom','right_bottom',[],(310,160,90,40)),('c','pr',7,'top','top',[(180,80),(920,80)],(850,220,90,40)),('pr','pa',8,'bottom','right',[(920,540),(765,540),(765,400)],(890,565,90,40)),('pa','b',9,'bottom','top',[],(565,540,90,40)),('b','u',10,'bottom','top',[],(565,820,90,40)),('u','db',11,'bottom','top',[],(565,1060,90,40)),('api','db',12,'left','left',[(350,145),(350,1205)],(260,790,90,40))],
        'Шаг 8 — отдельный подписанный webhook; возврат браузера не подтверждает зачисление. Шаг 12 — чтение подтверждённого баланса.')
    trajectory('19_path_support_audit','Траектории A5–A6: обращение, ответ и аудит',[
        ('c',30,100,300,90,'Клиент','identity','person'),('ui',390,100,340,90,'Web UI / Security','identity','filled'),('sup',390,380,340,100,'Support','support','filled'),('db3',30,650,300,120,'D3 VPS','vps','db'),('db5',770,650,300,120,'D5 Тикеты','support','db'),('staff',770,100,300,90,'Специалист поддержки','support','person'),('audit',390,920,340,100,'Audit / Unit of Work','audit','filled'),('db6',390,1150,340,120,'D6 Аудит','audit','db')],[
        ('c','ui',1,'right','left',[],(310,210,90,40)),('ui','sup',2,'bottom','top',[],(565,280,90,40)),('sup','db3',3,'left','top',[(180,430)],(130,530,90,40)),('sup','db5',4,'right','top',[(920,430)],(925,530,90,40)),('staff','ui',5,'left','right',[],(715,210,90,40)),('ui','sup',6,'right','right',[(750,145),(750,430)],(670,280,90,40)),('sup','db5',7,'bottom','bottom',[(560,840),(920,840)],(790,810,90,40)),('sup','audit',8,'bottom','top',[],(565,820,90,40)),('audit','db6',9,'bottom','top',[],(565,1070,90,40)),('ui','sup',10,'left','left',[(350,145),(350,430)],(260,280,90,40)),('ui','audit',11,'right','right',[(1090,145),(1090,970)],(980,930,90,40)),('audit','db6',12,'right','right',[(770,970),(770,1210)],(735,1090,90,40))],
        'Изменение тикета и INSERT аудита выполняются одной транзакцией. Публичное чтение тикета и служебное чтение аудита имеют разные права.')

def main():
    import build_diagrams
    old_font=build_diagrams.FONT
    build_diagrams.FONT='/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf'
    registration();support();deletion();architecture_paths()
    build_diagrams.FONT=old_font
    (Path(__file__).resolve().parents[1]/'work'/'bpmn_flows.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
