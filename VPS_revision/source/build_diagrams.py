from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from lxml import etree as E
import math

OUT=Path(__file__).resolve().parents[1]/'diagrams'
OUT.mkdir(exist_ok=True)
COL={'identity':'#2563eb','infra':'#0f766e','vps':'#7c3aed','money':'#b45309','support':'#be185d','audit':'#475569','ext':'#64748b'}
FONT='/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf'
if not Path(FONT).exists():
    FONT='/usr/share/fonts/google-noto/NotoSans-Regular.ttf'
class Diagram:
    def __init__(self,name,title,w=1100,h=1350):
        self.name=name; self.w=w; self.h=h; self.im=Image.new('RGB',(w*2,h*2),'#f8fafc'); self.d=ImageDraw.Draw(self.im)
        self.mx=E.Element('mxfile',host='app.diagrams.net'); dia=E.SubElement(self.mx,'diagram',name=title,id=name)
        model=E.SubElement(dia,'mxGraphModel',dx=str(w),dy=str(h),grid='1',gridSize='10',page='1',pageWidth=str(w),pageHeight=str(h))
        self.root=E.SubElement(model,'root'); E.SubElement(self.root,'mxCell',id='0'); E.SubElement(self.root,'mxCell',id='1',parent='0'); self.i=1; self.nodes={}
        self.text((30,18,w-60,44),title,26,'#0f172a'); self.d.line((60,128,(w-30)*2,128),fill='#cbd5e1',width=2)
    def uid(self): self.i+=1; return str(self.i)
    def text(self,box,t,size=21,color='#0f172a',center=True):
        x,y,w,h=box; f=ImageFont.truetype(FONT,size*2); lines=[]
        for line in t.split('\n'):
            words=line.split(' '); s=''
            for word in words:
                nxt=(s+' '+word).strip()
                if self.d.textlength(nxt,font=f)>w*2-16 and s: lines.append(s); s=word
                else: s=nxt
            lines.append(s)
        lh=int(size*2*1.33)
        if len(lines)*lh>h*2+3:
            print('TEXT_OVERFLOW',self.name,repr(t),round(len(lines)*lh/2),'>',h)
        yy=y*2+(h*2-len(lines)*lh)/2
        for line in lines:
            xx=x*2+(w*2-self.d.textlength(line,font=f))/2 if center else x*2+12
            self.d.text((xx,yy),line,font=f,fill=color); yy+=lh
        return len(lines)*lh/2
    def box(self,id,x,y,w,h,title,kind='box',group='vps',body='',size=21):
        c=COL.get(group,group); self.nodes[id]=(x,y,w,h); b=(x*2,y*2,(x+w)*2,(y+h)*2)
        shape='rounded=1;arcSize=12;'
        if kind=='diamond':
            self.d.polygon([(x*2,(y+h/2)*2),((x+w/2)*2,y*2),((x+w)*2,(y+h/2)*2),((x+w/2)*2,(y+h)*2)],fill='white',outline=c,width=3)
            self.text((x+15,y,w-30,h),title,size,c); shape='rhombus;'
        elif kind=='ellipse' or kind=='event' or kind=='end':
            self.d.ellipse(b,fill=c if kind=='end' else 'white',outline=c,width=3)
            if kind=='end': self.d.ellipse((x*2+7,y*2+7,(x+w)*2-7,(y+h)*2-7),outline='white',width=2)
            self.text((x,y,w,h),title,size,c); shape='ellipse;'
        elif kind=='table':
            self.d.rectangle(b,fill='white',outline=c,width=3)
            self.d.rectangle((x*2,y*2,(x+w)*2,(y+43)*2),fill=c)
            self.text((x,y,w,43),title,size,'white')
            self.text((x+4,y+48,w-8,h-53),body,size-2,center=False)
            shape='swimlane;startSize=43;horizontal=1;'
        elif kind=='store':
            self.d.line((x*2,(y+h)*2,x*2,y*2,(x+w)*2,y*2),fill=c,width=3)
            self.d.line((x*2,(y+h)*2,(x+w)*2,(y+h)*2),fill=c,width=3)
            self.d.line(((x+48)*2,y*2,(x+48)*2,(y+h)*2),fill=c,width=2)
            self.text((x+50,y,w-50,h),title,size,c); shape='shape=partialRectangle;right=0;'
        elif kind=='db':
            self.d.rounded_rectangle(b,radius=20,fill='white',outline=c,width=3)
            self.d.ellipse((x*2,y*2,(x+w)*2,(y+35)*2),fill='white',outline=c,width=3)
            self.text((x,y+32,w,h-32),title,size,c); shape='shape=cylinder3;'
        else:
            filled=kind in ('filled','person')
            self.d.rounded_rectangle(b,radius=16 if kind!='external' else 0,fill=c if filled else 'white',outline=c,width=3)
            self.text((x+6,y+3,w-12,h-6),title,size,'white' if filled else c)
            if kind=='external': shape='rounded=0;'
        value=title+('\n'+body if body else '')
        cell=E.SubElement(self.root,'mxCell',id=id,value=value,vertex='1',parent='1',style=shape+f'fillColor={c if kind in ("filled","person") else "#ffffff"};strokeColor={c};fontColor={"#ffffff" if kind in ("filled","person") else c};fontFamily=DejaVu Sans;fontSize={size};whiteSpace=wrap;html=0;')
        E.SubElement(cell,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
    def edge(self,a,b,label='',points=None,color='audit',dashed=False,start='bottom',end='top',label_at=None,arrow=True):
        c=COL.get(color,color)
        def port(id,p):
            x,y,w,h=self.nodes[id]
            return {'top':(x+w/2,y),'bottom':(x+w/2,y+h),'left':(x,y+h/2),'right':(x+w,y+h/2),
                    'left_top':(x,y+h*.25),'left_bottom':(x,y+h*.75),'right_top':(x+w,y+h*.25),'right_bottom':(x+w,y+h*.75)}[p]
        ps=[port(a,start)]+(points or [])+[port(b,end)]
        for p,q in zip(ps,ps[1:]):
            if dashed:
                n=max(1,int(math.dist(p,q)/12))
                for i in range(0,n,2):
                    aa=(p[0]+(q[0]-p[0])*i/n,p[1]+(q[1]-p[1])*i/n); bb=(p[0]+(q[0]-p[0])*min(i+1,n)/n,p[1]+(q[1]-p[1])*min(i+1,n)/n)
                    self.d.line(tuple(v*2 for pair in (aa,bb) for v in pair),fill=c,width=2)
            else:self.d.line(tuple(v*2 for pair in (p,q) for v in pair),fill=c,width=3)
        if arrow:
            p,q=ps[-2:]; ang=math.atan2(q[1]-p[1],q[0]-p[0]); tri=[q,(q[0]-12*math.cos(ang-.4),q[1]-12*math.sin(ang-.4)),(q[0]-12*math.cos(ang+.4),q[1]-12*math.sin(ang+.4))]
            self.d.polygon([(x*2,y*2) for x,y in tri],fill=c)
        if label:
            if label_at is None:
                p,q=max(zip(ps,ps[1:]),key=lambda pq:math.dist(*pq)); label_at=((p[0]+q[0])/2-100,(p[1]+q[1])/2-29,200,50)
            x,y,w,h=label_at; self.d.rectangle((x*2,y*2,(x+w)*2,(y+h)*2),fill='#f8fafc'); self.text(label_at,label,18,c)
        ports={'top':(.5,0),'bottom':(.5,1),'left':(0,.5),'right':(1,.5),'left_top':(0,.25),'left_bottom':(0,.75),'right_top':(1,.25),'right_bottom':(1,.75)}
        sx,sy=ports[start];ex,ey=ports[end]
        cell=E.SubElement(self.root,'mxCell',id=self.uid()+'e',value=label,edge='1',source=a,target=b,parent='1',style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;strokeColor={c};fontSize=18;labelBackgroundColor=#f8fafc;endArrow={"block" if arrow else "none"};dashed={int(dashed)};exitX={sx};exitY={sy};entryX={ex};entryY={ey};')
        geo=E.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
        if points:
            ar=E.SubElement(geo,'Array',attrib={'as':'points'})
            for x,y in points:E.SubElement(ar,'mxPoint',x=str(x),y=str(y))
    def note(self,y,t): self.text((30,y,self.w-60,65),t,18,'#475569')
    def save(self):
        self.im.save(OUT/(self.name+'.png'),dpi=(300,300)); E.ElementTree(self.mx).write(str(OUT/(self.name+'.drawio')),encoding='utf-8',xml_declaration=True)

def chen():
    d=Diagram('01_chen','Инфологическая модель: сущности и отношения',1100,1380)
    # Three vertical chains, with attributes outside the relation corridors.
    for id,x,y,title,g,attrs in [
        ('u',60,170,'Пользователь','identity',['id (ключ)','email; роль']),('a',60,610,'Лицевой счёт','money',['id (ключ)','валюта RUB']),('l',60,1050,'Проводка','money',['id; сумма','ключ операции']),
        ('v',430,610,'VPS','vps',['id (ключ)','состояние']),('t',430,170,'Версия тарифа','vps',['код; версия','CPU; RAM; SSD']),('s',430,1050,'Обращение','support',['id; статус','описание; ответ']),
        ('dc',800,170,'Дата-центр','infra',['id (ключ)','название']),('n',800,610,'Нода','infra',['id (ключ)','лимиты ресурсов']),('au',800,1050,'Событие аудита','audit',['id; время UTC','действие'])]:
        d.box(id,x,y,235,66,title,'filled',g,size=20)
        d.box(id+'a',x,y-74,110,48,attrs[0],'ellipse',g,size=16); d.box(id+'b',x+120,y-74,115,48,attrs[1],'ellipse',g,size=16)
        d.edge(id+'a',id,arrow=False,color=g); d.edge(id+'b',id,arrow=False,color=g)
    for a,b,r,card,g in [('u','a','владеет','1 : 1 (клиент)','identity'),('a','l','содержит','1 : 0..N','money'),('t','v','определяет','1 : 0..N','vps'),('v','s','связан с','1 : 0..N','support'),('dc','n','включает','1 : 0..N','infra')]:
        x,y,w,h=d.nodes[a]; x2,y2,_,_=d.nodes[b]; mid=(y+h+y2)/2
        rid='rel_'+a+'_'+b; d.box(rid,x+40,mid-48,155,96,r,'diamond',g,size=18)
        d.edge(a,rid,color=g,arrow=False); d.edge(rid,b,card,color=g,arrow=False,label_at=(x+30,mid+87,180,44))
    d.box('owns',316,605,100,78,'арендует','diamond','identity',size=15)
    d.edge('u','owns',points=[(355,203)],start='right',end='top',arrow=False,color='identity',label='1',label_at=(307,250,45,32)); d.edge('owns','v','0..N',start='right',end='left',arrow=False,color='identity',label_at=(350,686,85,35))
    d.box('place',683,605,104,78,'размещён','diamond','infra',size=15)
    d.edge('v','place',start='right',end='left',arrow=False,color='infra'); d.edge('place','n',start='right',end='left',arrow=False,color='infra')
    d.text((650,702,175,54),'VPS N : 1 нода',17,COL['infra'])
    d.box('initiates',810,1150,180,80,'инициирует','diamond','audit',size=18)
    d.edge('u','initiates','0..1 : 0..N',[(15,203),(15,1190)],start='left',end='left',arrow=False,label_at=(330,1165,220,44))
    d.edge('initiates','au',start='top',end='bottom',arrow=False)
    d.note(1240,'Дополнительные отношения: пользователь 1 : 0..N обращений (автор / исполнитель); пользователь 0..1 : 0..N событий аудита. Системное событие не имеет инициатора.'); d.save()

SCHEMA=[
 ('users','identity','PK id : bigint\nUQ email : text\npassword_hash : text\nrole : enum\ncreated_at : timestamptz'),
 ('user_accounts','money','PK id : bigint\nFK UQ user_id → users\ncurrency = RUB\ncreated_at : timestamptz'),
 ('financial_ledger','money','PK id : bigint\nFK account_id → user_accounts\nFK vps_id? → vps_instances\namount : numeric(18,2)\nUQ operation_key : text\nprovider_payment_id?\nperiod_start?; created_at'),
 ('datacenters','infra','PK id : bigint\nname : text\nlocation : text'),
 ('node_servers','infra','PK id : bigint\nFK datacenter_id\nname; state\ncpu_total : integer\nram_mb; ssd_gb : bigint\nendpoint_ref : text'),
 ('tariff_plans','vps','PK id : bigint\ncode; version\ncpu; ram_mb; ssd_gb\nprice_hour : numeric(18,2)\nvalid_from; valid_to?\nUQ (code, version)'),
 ('vps_instances','vps','PK id : bigint\nFK user_id → users\nFK node_id → node_servers\nFK tariff_version_id\nUQ request_key\nUQ (node_id, vm_key)\nstate; paid_until?\nlease_until?; attempt_count\nrevision; last_error?\nUQ (id, user_id)'),
 ('support_tickets','support','PK id : bigint\nFK (vps_id, user_id)\nFK user_id → users\nFK assignee_id? → users\nstatus; subject; description\nanswer?; created_at'),
 ('system_audit_log','audit','PK id : bigint\nFK actor_id? → users\nentity_type; entity_id\naction; payload : jsonb\ncreated_at : timestamptz')]

def er():
    d=Diagram('02_er','Реляционная модель: девять таблиц',1100,1430)
    pos=[(30,100,310,220),(30,415,310,200),(30,770,310,300),(760,100,310,155),(760,375,310,270),(760,800,310,260),(395,380,310,390),(395,990,310,275),(395,100,310,210)]
    for (id,g,b),(x,y,w,h) in zip(SCHEMA,pos):d.box(id,x,y,w,h,id,'table',g,b,19)
    for a,b,points,st,en,label,la in [
        ('users','user_accounts',[], 'bottom','top','1 — 0..1',(65,339,200,40)),
        ('user_accounts','financial_ledger',[],'bottom','top','1 — 0..N',(55,665,220,40)),
        ('datacenters','node_servers',[],'bottom','top','1 — 0..N',(810,290,220,40)),
        ('node_servers','vps_instances',[],'left','right','1 — 0..N',(695,647,125,40)),
        ('tariff_plans','vps_instances',[(730,930),(730,745)],'left','right','1 — 0..N',(700,838,145,40)),
        ('users','vps_instances',[(365,210),(365,450)],'right','left','1 — 0..N',(335,300,130,40)),
        ('vps_instances','support_tickets',[],'bottom','top','1 — 0..N',(430,862,230,40)),
        ('users','system_audit_log',[],'right','left','0..1 — 0..N',(330,105,140,40)),
        ('vps_instances','financial_ledger',[(365,690),(365,920)],'left','right','0..1 — 0..N',(312,720,160,40))]:
        d.edge(a,b,label,points,color=next(g for id,g,_ in SCHEMA if id==a),start=st,end=en,label_at=la,arrow=False)
    d.note(1310,'PK — первичный ключ; FK — внешний ключ; UQ — уникальность; ? — NULL. Ролевые связи тикета и аудита заданы полями FK. Кратности читаются от первой таблицы ко второй.'); d.save()

def context():
    d=Diagram('03_dfd_context','DFD • уровень 0: граница системы',1100,1100)
    for args in [('client',50,120,280,100,'Клиент','external','identity'),('staff',750,120,300,100,'Администратор /\nподдержка','external','identity'),('sys',360,460,380,170,'0. Система аренды\nвиртуальных серверов','filled','infra'),('pay',30,900,330,100,'Платёжный провайдер','external','money'),('hyp',750,900,300,100,'Гипервизор','external','ext')]:d.box(*args)
    d.edge('client','sys','Регистрация; заказ;\nкоманда VPS; тикет',[(190,340),(460,340)],end='top',color='identity',label_at=(75,242,320,70))
    d.edge('sys','client','Профиль; баланс;\nстатус VPS; ответ',[(300,550),(300,260),(50,260)],start='left',end='left',color='infra',label_at=(30,390,270,65))
    d.edge('staff','sys','Ноды; тарифы;\nрешение обращения',[(900,345),(650,345)],color='identity',label_at=(730,250,330,70))
    d.edge('sys','staff','Результаты; загрузка;\nочередь тикетов',[(1080,550),(1080,165)],start='right',end='right',color='infra',label_at=(780,470,295,75))
    d.edge('sys','pay','Запрос оплаты',[(460,750),(195,750)],color='money',label_at=(110,687,275,50))
    d.edge('pay','sys','Подписанный результат',[(45,840),(45,650),(360,650)],start='top',end='left',color='money',label_at=(35,780,320,50))
    d.edge('sys','hyp','Команда / запрос ВМ',[(650,750),(900,750)],color='ext',label_at=(720,687,330,50))
    d.edge('hyp','sys','Результат / состояние ВМ',[(1065,950),(1065,650),(740,650)],start='right',end='right',color='ext',label_at=(720,790,340,55))
    d.note(1020,'На контекстном уровне внутренние хранилища не показываются. Карточные реквизиты обрабатывает платёжный провайдер.'); d.save()

def dfd1():
    d=Diagram('04_dfd_level1','DFD • уровень 1: функции и хранилища',1100,1440)
    for args in [('c',30,100,300,75,'Клиент','external','identity'),('s',755,100,315,75,'Администратор / поддержка','external','identity'),('a1',30,300,300,100,'1.0 Регистрация\nи профиль','filled','identity'),('a2',755,300,315,100,'2.0 Инфраструктура\nи версии тарифов','filled','infra'),('a3',380,560,330,120,'3.0 Аренда и\nуправление VPS','filled','vps'),('a4',30,850,300,110,'4.0 Финансовый учёт','filled','money'),('a5',755,850,315,110,'5.0 Поддержка','filled','support'),('a6',380,1160,330,90,'6.0 Аудит','filled','audit'),('pay',30,1240,300,75,'Платёжный провайдер','external','money'),('hyp',755,1240,315,75,'Гипервизор','external','ext')]:d.box(*args,size=20)
    for id,x,y,t,g in [('d1',30,480,'D1 Профили / счета','identity'),('d2',755,480,'D2 Ноды / тарифы','infra'),('d3',380,770,'D3 VPS','vps'),('d4',30,1050,'D4 Проводки','money'),('d5',755,1050,'D5 Тикеты','support'),('d6',380,1320,'D6 Аудит','audit')]:d.box(id,x,y,315 if x!=380 else 330,62,t,'store',g,size=19)
    for a,b,label,st,en,pts,la in [
        ('c','a1','Данные профиля / результат','bottom','top',[],(25,211,320,55)),('s','a2','Ноды, тарифы / результат','bottom','top',[],(750,211,320,55)),
        ('a1','d1','Профиль; счёт','bottom','top',[],(38,417,280,45)),('a2','d2','Лимиты; версии','bottom','top',[],(772,417,280,45)),
        ('d1','a3','Владелец / счёт','right','left',[(350,511),(350,610)],(265,538,210,45)),('d2','a3','Доступная конфигурация','left','right',[(730,511),(730,610)],(710,540,360,45)),
        ('c','a3','Заявка / статус VPS','right','top',[(550,137)],(345,230,330,55)),('a3','d3','Состояние; резерв','bottom','top',[],(407,698,280,45)),
        ('a3','a4','Начисление / результат','left','top',[(180,620)],(50,690,300,55)),('a4','d4','Проводки / история','bottom','top',[],(40,982,295,45)),
        ('a3','a5','Контекст VPS','right','top',[(910,620)],(770,687,275,50)),('a5','d5','Обращение / решение','bottom','top',[],(770,982,290,45)),
        ('pay','a4','Результат оплаты / запрос','left','left',[(15,1277),(15,905)],(22,1140,320,55)),
        ('a3','hyp','Команда / состояние ВМ','right','right',[(1090,620),(1090,1277)],(755,1150,320,55)),
        ('a3','a6','Критическое изменение','bottom','top',[(710,720),(710,1120),(545,1120)],(400,1080,305,45)),
        ('a6','d6','Событие аудита','bottom','top',[],(397,1267,295,45))]: d.edge(a,b,label,pts,start=st,end=en,label_at=la)
    d.save()

def dfd2():
    d=Diagram('05_dfd_level2','DFD • уровень 2: процесс 3.0 «Аренда VPS»',1100,1370)
    for id,y,t in [('c',100,'Клиент: заявка / команда и ключ'),('p1',290,'3.1 Проверить доступ и параметры'),('p2',520,'3.2 Подготовить операцию,\nрезерв и оплату'),('p3',790,'3.3 Выполнить / сверить\nкоманду ВМ'),('p4',1080,'3.4 Зафиксировать результат')]:d.box(id,355,y,400,100,t,'external' if id=='c' else 'filled','vps')
    for id,x,y,t,g in [('d1',25,290,'D1 Профиль / счёт','identity'),('d2',25,520,'D2 Ноды / тарифы','infra'),('d3',25,790,'D3 VPS','vps'),('d4',800,520,'4.0 Финансовый учёт','money'),('hyp',800,790,'Гипервизор','ext'),('d6',800,1080,'6.0 Аудит','audit')]:d.box(id,x,y,275,90,t,'store' if id.startswith('d') and id in ('d1','d2','d3') else 'external',g,size=19)
    for a,b,l in [('c','p1','Заявка'),('p1','p2','Разрешённая команда'),('p2','p3','Устойчивое задание'),('p3','p4','Подтверждённое состояние')]:d.edge(a,b,l,label_at=(380,(d.nodes[a][1]+100+d.nodes[b][1])/2-24,350,50),color='vps')
    for a,b,l,st,en in [('d1','p1','Профиль','right','left'),('d2','p2','Лимиты','right','left'),('p2','d4','Списание','right_top','left_top'),('p3','hyp','Команда ВМ','right_top','left_top'),('p4','d6','Событие','right','left')]:d.edge(a,b,l,start=st,end=en,label_at=(295 if st=='right' and a.startswith('d') else 744,d.nodes[a][1]-48,150,45))
    d.edge('d4','p2','Результат',start='left_bottom',end='right_bottom',label_at=(760,625,210,42),color='money')
    d.edge('hyp','p3','Состояние ВМ',start='left_bottom',end='right_bottom',label_at=(755,902,265,42),color='ext')
    d.edge('p2','d3','Заказ / операция',[(320,570),(320,815)],start='left',end='right_top',label_at=(25,672,280,45),color='vps')
    d.edge('d3','p2','Резерв / состояние',[(335,857),(335,595)],start='right_bottom',end='left_bottom',label_at=(20,895,280,45),color='vps')
    d.edge('p4','d3','Итоговое состояние',[(162,1130)],start='left',end='bottom',label_at=(20,1000,280,45),color='vps')
    d.edge('p4','d4','Компенсация',[(785,1105),(785,690),(937,690)],start='right_top',end='bottom',label_at=(800,695,270,45),color='money')
    d.edge('d4','p4','Финансовый итог',[(1095,587),(1095,1185),(775,1185),(775,1155)],start='right_bottom',end='right_bottom',label_at=(790,1160,285,45),color='money')
    d.edge('p4','c','Результат аренды',[(320,1130),(320,220),(555,220)],start='left',end='bottom',label_at=(25,1200,300,55),color='vps')
    d.edge('p2','d6','Принятая операция',[(1085,545),(1085,1200),(937,1200)],start='right_top',end='bottom',label_at=(790,1210,280,45))
    d.note(1270,'3.2 сохраняет команду и аудит; при необходимости — оплату и резерв в той же транзакции. Внешний вызов 3.3 выполняется после commit.');d.save()

def dfd_balanced():
    def row(d,n,y,title,actor,store,g,incoming,outgoing,write,read):
        d.box('p'+str(n),345,y,400,100,f'{n}.0 {title}','filled',g,size=22)
        d.box('e'+str(n),25,y,235,100,actor,'external','identity',size=20)
        d.box('d'+str(n),830,y,245,100,store,'store',g,size=19)
        d.edge('e'+str(n),'p'+str(n),incoming,start='right_top',end='left_top',color=g,label_at=(20,y-66,310,60))
        d.edge('p'+str(n),'e'+str(n),outgoing,start='left_bottom',end='right_bottom',color=g,label_at=(20,y+108,310,58))
        d.edge('p'+str(n),'d'+str(n),write,start='right_top',end='left_top',color=g,label_at=(775,y-66,305,60))
        d.edge('d'+str(n),'p'+str(n),read,start='left_bottom',end='right_bottom',color=g,label_at=(775,y+108,305,58))
    def audit(d,id,y):
        d.box('audit'+id,415,y,260,62,'6.0 Аудит (копия)','box','audit',size=19)
        d.edge('p'+id,'audit'+id,'Событие изменения',color='audit',label_at=(375,y-55,340,42))
    d=Diagram('04_dfd_level1','DFD • уровень 1, лист 1: процессы 1.0–3.0',1100,1450)
    row(d,1,170,'Регистрация и профиль','Клиент','D1 Профили / счета','identity','Регистрационные данные','Профиль / отказ','Новый профиль и счёт','Текущий профиль')
    audit(d,'1',350)
    row(d,2,570,'Инфраструктура','Администратор','D2 Ноды / тарифы','infra','Ноды и версии тарифов','Результат / загрузка','Лимиты; новая версия','Сохранённая конфигурация')
    audit(d,'2',750)
    row(d,3,970,'Аренда и управление VPS','Клиент','D3 VPS','vps','Заявка / команда VPS','Принятая команда / статус','Заказ; состояние; резерв','Текущее состояние VPS')
    d.box('d1read',25,1180,245,65,'D1 Профили / счета','store','identity',size=18)
    d.box('d2read',25,1280,245,65,'D2 Ноды / тарифы','store','infra',size=18)
    d.box('a4',400,1225,300,85,'4.0 Финансовый учёт\n(копия)','box','money',size=19)
    d.box('hyp',830,1185,245,100,'Гипервизор','external','ext',size=20)
    d.box('audit3',830,1330,245,65,'6.0 Аудит (копия)','box','audit',size=18)
    d.edge('d1read','p3','Владелец / счёт',[(300,1212),(300,1045)],start='right',end='left_bottom',label_at=(24,1132,280,42),color='identity')
    d.edge('d2read','p3','Свободная конфигурация',[(315,1312),(315,995)],start='right',end='left_top',label_at=(20,1350,310,45),color='infra')
    d.edge('p3','a4','Начисление',color='money',label_at=(405,1140,280,40))
    d.edge('a4','p3','Результат',[(750,1268),(750,1125),(700,1125)],start='right',end='bottom',color='money',label_at=(630,1190,170,38))
    d.edge('p3','hyp','Команда ВМ',[(790,995),(790,1210)],start='right_top',end='left_top',color='ext',label_at=(820,1138,260,40))
    d.edge('hyp','p3','Состояние ВМ',[(810,1260),(810,1045)],start='left_bottom',end='right_bottom',color='ext',label_at=(800,1285,285,40))
    d.edge('p3','audit3','Событие',[(770,1045),(770,1305),(952,1305)],start='right_bottom',end='top',label_at=(830,1400,240,35))
    d.save()
    d=Diagram('04b_dfd_level1','DFD • уровень 1, лист 2: процессы 4.0–6.0',1100,1460)
    row(d,4,180,'Финансовый учёт','Клиент','D4 Проводки','money','Запрос пополнения / баланса','Платёжная ссылка / баланс','Новая проводка','История операций')
    d.box('provider',25,395,245,85,'Платёжный провайдер','external','money',size=19)
    d.box('account',830,395,245,85,'D1 Профили / счета','store','identity',size=18)
    audit(d,'4',395)
    d.edge('p4','provider','Запрос оплаты',[(310,205),(310,415)],start='left_top',end='right_top',color='money',label_at=(25,340,280,40))
    d.edge('provider','p4','Подписанный результат',[(330,459),(330,255)],start='right_bottom',end='left_bottom',color='money',label_at=(15,492,320,45))
    d.edge('account','p4','Счёт получателя',[(795,438),(795,280)],start='left',end='bottom',color='identity',label_at=(800,490,280,40))
    row(d,5,760,'Поддержка','Клиент','D5 Тикеты','support','Заявка / решение клиента','Статус / последний ответ','Обращение; ответ; статус','Текущее обращение')
    d.box('staff5',25,970,245,100,'Специалист поддержки','external','support',size=20)
    d.box('vpsread',830,970,245,100,'D3 VPS','store','vps',size=20)
    audit(d,'5',970)
    d.edge('staff5','p5','Назначение / ответ',[(310,995),(310,835)],start='right_top',end='left_bottom',color='support',label_at=(10,1090,320,45))
    d.edge('p5','staff5','Очередь / контекст',[(330,785),(330,1045)],start='left_top',end='right_bottom',color='support',label_at=(10,914,320,42))
    d.edge('vpsread','p5','Владелец / состояние VPS',[(795,1020),(795,860)],start='left',end='bottom',color='vps',label_at=(775,1090,310,45))
    row(d,6,1260,'Аудит','Уполномоченный\nперсонал','D6 Аудит','audit','Запрос истории','Разрешённые события','Событие изменения','История изменений')
    d.note(580,'Повторяющиеся блоки с одинаковым номером обозначают один процесс или хранилище. Потоки критических событий из 1.0–5.0 входят в 6.0 на обоих листах.');d.save()

def bpmn(name,title,steps,store,alternative):
    d=Diagram(name,title,1100,1400)
    # Task flow and data associations; no technical components are sequence-flow nodes.
    d.box('start',520,100,46,46,'','event','infra')
    ys=[220,450,710,970]
    for i,(t,g) in enumerate(steps):d.box('t'+str(i),340,ys[i],410,100,t,'box',g,size=21)
    d.box('gate',460,595,170,86,'Успешно?','diamond','infra',size=19)
    d.box('end',520,1210,46,46,'','end','infra')
    d.edge('start','t0',color='infra'); d.edge('t0','t1',color='infra');d.edge('t1','gate',color='infra')
    d.edge('gate','t2','Да',color='infra',label_at=(548,682,55,35));d.edge('t2','t3',color='infra');d.edge('t3','end',color='infra')
    d.box('alt',810,570,260,145,alternative,'box','support',size=20)
    d.box('altend',915,810,46,46,'','end','support')
    d.edge('gate','alt','Нет',start='right',end='left',color='support',label_at=(673,590,75,35)); d.edge('alt','altend',color='support')
    d.box('db',25,960,260,140,store,'db','infra',size=20)
    d.edge('t3','db','Данные',start='left',end='right',dashed=True,arrow=False,color='infra',label_at=(268,927,100,35))
    d.box('mod',25,450,260,105,'«component»\nПрикладной модуль','external','audit',size=19)
    d.edge('mod','t1','Выполняет',start='right',end='left',dashed=True,arrow=False,label_at=(250,407,130,35))
    d.note(1300,'Круг — начало; круг с толстой границей — конец; скруглённый блок — задача; ромб — XOR. Пунктирные связи показывают данные и реализацию, а не порядок задач.'); d.save()

def lifecycle():
    d=Diagram('09_vps_states','Жизненный цикл VPS и сохранение ресурсов',1100,1330)
    for id,x,y,t,g in [('p',380,100,'PROVISIONING','vps'),('a',380,390,'ACTIVE','infra'),('b',40,660,'BLOCKING','money'),('s',40,950,'SUSPENDED','money'),('del',730,660,'DELETING','support'),('done',730,950,'DELETED','audit'),('fail',730,100,'FAILED','audit')]:d.box(id,x,y,300,85,t,'filled',g,size=23)
    d.edge('p','a','ВМ найдена / создана',color='infra',label_at=(365,260,330,55))
    d.edge('p','fail','ВМ отсутствует;\nкомпенсация',start='right',end='left',label_at=(650,194,400,65))
    d.edge('a','b','Не оплачен следующий час',[(190,432)],start='left',color='money',label_at=(30,510,350,55))
    d.edge('b','s','Остановка подтверждена',color='money',label_at=(28,806,330,55))
    d.edge('s','a','Пополнение; новый час;\nподтверждение запуска',[(360,992),(360,510),(530,510)],start='right',end='bottom',color='infra',label_at=(375,785,330,70))
    d.edge('a','del','Удаление принято',[(880,432)],start='right',color='support',label_at=(745,510,300,55))
    d.edge('s','del','Удаление',[(530,992),(530,900),(880,900)],start='right',end='bottom',color='support',label_at=(540,925,200,45))
    d.edge('del','done','Отсутствие ВМ подтверждено',color='support',label_at=(715,798,360,65))
    d.note(1110,'Ресурсы заняты в PROVISIONING, ACTIVE, BLOCKING, SUSPENDED и DELETING. В FAILED и DELETED резерв освобождён после проверки гипервизора.');d.note(1210,'При неопределённом результате состояние сохраняется и выполняется сверка. Действие возобновления использует отдельную фазу запуска в SUSPENDED.');d.save()

def architecture():
    d=Diagram('10_architecture','Обобщённая архитектура: модули и окружение',1100,1420)
    for id,x,y,w,h,t,g,k in [('client',30,100,300,90,'Клиент','identity','person'),('staff',770,100,300,90,'Персонал','identity','person'),('web',370,100,360,110,'Web UI\nКабинет / панели','identity','filled'),('api',370,340,360,100,'Backend API\nМаршрутизация; доступ','vps','filled'),('identity',30,580,300,100,'Identity\nПрофиль и счёт','identity','box'),('infra',770,580,300,100,'Infrastructure\nНоды и тарифы','infra','box'),('prov',370,580,360,110,'Provisioning\nСостояния и резерв','vps','box'),('bill',30,830,300,100,'Billing\nПроводки и периоды','money','box'),('support',770,830,300,100,'Support / Audit\nОбращения и события','support','box'),('uow',370,830,360,100,'Unit of Work\nТранзакции и блокировки','audit','filled'),('db',370,1090,360,120,'PostgreSQL\nДевять таблиц','infra','db'),('worker',30,1090,300,120,'Worker\nVM; billing; reconcile','vps','filled'),('hyp',30,1310,300,80,'Гипервизор','ext','external'),('pay',770,1090,300,120,'Платёжный провайдер','money','external')]:d.box(id,x,y,w,h,t,k,g,size=20)
    for a,b,l,st,en,pts,la in [('client','web','HTTPS','right','left',[],(275,220,130,40)),('staff','web','HTTPS','left','right',[],(705,220,130,40)),('web','api','JSON / HTTPS','bottom','top',[],(410,250,270,45)),('api','prov','Команда','bottom','top',[],(440,475,220,45)),('api','identity','Профиль','left','top',[(180,390)],(35,450,280,45)),('api','infra','Инфраструктура','right','top',[(920,390)],(770,450,280,45)),('prov','bill','Начисление','left','top',[(180,635)],(25,735,300,45)),('prov','support','Контекст / событие','right','top',[(920,635)],(755,735,320,45)),('prov','uow','Изменения','bottom','top',[],(425,736,250,45)),('uow','db','SQL / commit','bottom','top',[],(410,985,280,45)),('worker','db','Задания / данные','right','left',[],(270,1215,330,45)),('worker','hyp','create / inspect / stop / delete','bottom','top',[],(12,1233,335,55)),('pay','api','Подписанный webhook', 'right','right',[(1090,1150),(1090,390)],(770,1000,320,55))]:d.edge(a,b,l,pts,start=st,end=en,label_at=la)
    d.save()

def c4_context():
    d=Diagram('11_c4_context','C4 • уровень 1: системный контекст',1100,1080)
    d.box('c',30,110,300,100,'Клиент\n[Person]','person','identity');d.box('s',770,110,300,100,'Персонал\n[Person]','person','identity')
    d.box('sys',340,420,420,190,'Система аренды VPS/VDS\n[Software System]\nАренда, баланс, инфраструктура,\nподдержка и аудит','filled','vps',size=23)
    d.box('pay',30,840,370,130,'Платёжный провайдер\n[External Software System]','filled','ext')
    d.box('hyp',700,840,370,130,'Гипервизор\n[External Software System]','filled','ext')
    d.edge('c','sys','Заказывает и управляет VPS\nHTTPS',[(180,315),(440,315)],label_at=(45,242,350,70),color='identity')
    d.edge('s','sys','Ведёт инфраструктуру\nи обращения; HTTPS',[(920,315),(660,315)],label_at=(730,242,350,70),color='identity')
    d.edge('sys','pay','Создаёт платёж; получает\nподписанный результат; HTTPS',[(450,725),(215,725)],label_at=(30,645,390,70),color='money')
    d.edge('sys','hyp','Управляет ВМ и сверяет\nсостояние; API / TLS',[(650,725),(885,725)],label_at=(700,645,380,70),color='ext')
    d.note(995,'Граница Software System включает UI, API, Worker и PostgreSQL. Платёжный провайдер и гипервизор — внешние системы.');d.save()

def c4_containers():
    d=Diagram('12_c4_containers','C4 • уровень 2: контейнеры',1100,1350)
    for id,x,y,w,h,t,g,k in [('person',365,100,370,90,'Клиент / персонал [Person]','identity','person'),('web',365,330,370,140,'Web UI [Container]\nTypeScript / React\nКабинет и рабочие панели','identity','filled'),('api',365,630,370,150,'Backend API [Container]\nPython / FastAPI\nПравила; доступ; webhook','vps','filled'),('worker',30,970,320,150,'Worker [Container]\nPython\nVM; сверка; биллинг','vps','filled'),('db',710,970,360,150,'PostgreSQL [Container: DB]\nТаблицы; ограничения; аудит','infra','db'),('pay',30,630,280,150,'Платёжный провайдер\n[External System]','ext','external'),('hyp',30,1220,320,90,'Гипервизор\n[External System]','ext','external')]:d.box(id,x,y,w,h,t,k,g,size=20)
    for a,b,l,st,en,p,la in [('person','web','HTTPS','bottom','top',[],(420,232,260,45)),('web','api','JSON / HTTPS','bottom','top',[],(400,525,300,50)),('api','db','SQL / транзакции','right','top',[(890,705)],(750,825,330,55)),('worker','db','SQL; захват заданий','right','left',[],(365,1010,330,60)),('api','pay','Платёж / webhook\nHTTPS','left','right',[],(20,825,325,70)),('worker','hyp','API / TLS','bottom','top',[],(45,1145,275,45))]:d.edge(a,b,l,p,start=st,end=en,label_at=la)
    d.note(80,'')
    d.save()

def components():
    d=Diagram('13_c4_components','C4 • уровень 3: компоненты Backend API',1100,1410)
    for id,x,y,w,h,t,g,k in [('web',30,100,300,100,'Web UI\n[Container]','identity','external'),('pay',770,100,300,100,'Платёжный провайдер\n[External System]','ext','external'),('sec',370,100,360,100,'Security / Router\n[Component]','identity','filled'),('identity',30,390,300,130,'Identity\nПрофиль; создание счёта','identity','box'),('prov',370,390,360,130,'Provisioning\nАренда; переходы VPS','vps','box'),('infra',770,390,300,130,'Infrastructure\nНоды; версии тарифов','infra','box'),('billing',30,710,300,130,'Billing\nПериоды; журнал; баланс','money','box'),('payment',770,710,300,130,'Payment Adapter\nПодпись; сумма; ключ','money','box'),('support',370,710,360,130,'Support / Audit\nТикеты; события','support','box'),('uow',165,1040,770,110,'Unit of Work / Repository [Component]\nОбщие транзакции; порядок блокировок; доступ к данным','audit','filled'),('db',365,1260,370,120,'PostgreSQL\n[Container: Database]','infra','db')]:d.box(id,x,y,w,h,t,k,g,size=20)
    for a,b,l,st,en,p,la in [('web','sec','JSON / HTTPS','right','left',[],(250,228,220,40)),('sec','prov','Разрешённая команда','bottom','top',[],(375,270,350,45)),('sec','identity','Профиль','left','top',[(180,260)],(25,300,290,45)),('sec','infra','Лимиты / тарифы','right','top',[(920,260)],(770,300,290,45)),('pay','payment','webhook','right','right',[(1090,150),(1090,775)],(785,570,270,45)),('payment','billing','Проверенное зачисление','bottom','bottom',[(920,935),(180,935)],(345,905,390,45)),('prov','billing','Стоимость / проводка','left','top',[(180,455)],(20,590,310,55)),('prov','support','Событие / контекст','bottom','top',[],(380,590,340,55)),('support','uow','Изменения','bottom','top',[],(405,974,280,45)),('uow','db','SQL','bottom','top',[],(430,1181,240,45))]:d.edge(a,b,l,p,start=st,end=en,label_at=la)
    d.save()

def quality():
    d=Diagram('14_quality','Модель заинтересованности сторон (нотация Чена)',1100,1320)
    d.box('prod',375,550,350,130,'Проект системы\nаренды VPS/VDS','filled','vps',size=24)
    data=[('c',30,100,'Клиенты','q = 0,88; w = 0,30','identity'),('o',770,100,'Владелец сервиса','q = 0,80; w = 0,15','money'),('a',30,550,'Администраторы','q = 0,90; w = 0,15','infra'),('p',770,550,'Внешние партнёры','q = 0,82; w = 0,10','ext'),('s',30,1050,'Поддержка','q = 0,84; w = 0,15','support'),('dev',770,1050,'Разработка /\nэксплуатация','q = 0,86; w = 0,15','audit')]
    for id,x,y,t,q,g in data:
        d.box(id,x,y,300,90,t,'filled',g,size=21); d.box(id+'q',x,y+110,300,64,q,'ellipse',g,size=20)
        rx=385 if x==30 else 590; ry=300 if y==100 else 745 if y==550 else 915
        d.box(id+'r',rx,ry,125,80,'интерес','diamond',g,size=18)
        d.edge(id+'q',id+'r',arrow=False,color=g,start='right' if x==30 else 'left',end='left' if x==30 else 'right')
        d.edge(id,id+'r',arrow=False,color=g,start='right' if x==30 else 'left',end='top' if y==100 else 'left' if x==30 else 'right')
        d.edge(id+'r','prod',arrow=False,color=g,start='bottom' if y==100 else 'top',end='top' if y==100 else 'bottom')
    d.note(1220,'Q = Σ(w × q) = 0,856. Индексы являются иллюстративной экспертной оценкой проекта; измерения готового продукта не проводились.');d.save()

if __name__=='__main__':
    chen();er();context();dfd_balanced();dfd2()
    bpmn('06_bpmn_registration','BPMN • регистрация клиента',[
        ('Клиент: отправить форму','identity'),('Identity: проверить формат\nи уникальность email','identity'),('Identity: создать пользователя\nи лицевой счёт атомарно','identity'),('Система: вернуть профиль\nи результат регистрации','identity')],'users / user_accounts','Вернуть ошибку;\nпри конфликте UNIQUE\nоткатить транзакцию')
    bpmn('07_bpmn_support','BPMN • создание и обработка обращения',[
        ('Клиент: выбрать VPS\nи описать проблему','support'),('Support: проверить владельца\nи создать тикет OPEN','support'),('Специалист: IN_PROGRESS;\nответ → RESOLVED','support'),('Клиент: принять решение\nRESOLVED → CLOSED','support')],'support_tickets\nсвязь с VPS','Чужой VPS: отказ.\nТикет не сохраняется')
    bpmn('08_bpmn_delete','BPMN • удаление VPS: основной и отложенный путь',[
        ('Клиент: запросить удаление;\nProvisioning: DELETING','vps'),('Worker: удалить / сверить ВМ\nпо устойчивому vm_key','vps'),('Provisioning: DELETED;\nосвободить резерв атомарно','vps'),('Система: сохранить историю\nи вернуть итог клиенту','vps')],'vps_instances\nfinancial_ledger\nsystem_audit_log','Тайм-аут: сохранить\nDELETING и резерв;\nзапланировать сверку')
    lifecycle();architecture();c4_context();c4_containers();components();quality()
    from build_supplement import main as supplement
    supplement()
    print('Built',len(list(OUT.glob('*.png'))),'diagrams')
