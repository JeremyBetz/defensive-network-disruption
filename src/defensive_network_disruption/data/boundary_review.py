"""Restricted syntax projection and coordinate-only diagnostics for Session 12c."""
import csv
import io
import json
import math
import re
from statistics import median
from .receiver_choices import clock_microseconds,select_decision_frame,attack_sign,attacking_xy,active_in_period

_STRING=re.compile(r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"')
_SCALAR=re.compile(r'(?:-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null)')


class View:
    """JSON spans; unselected scalar values are never decoded."""
    def __init__(self,text):
        self.text=text
        try:
            self.end=self.skip(self.ws(0))
            if self.ws(self.end)!=len(text):raise ValueError()
        except (ValueError,IndexError,RecursionError):raise ValueError('json_syntax_invalid') from None
    def ws(self,i):
        while i<len(self.text) and self.text[i] in ' \r\n\t':i+=1
        return i
    def skip(self,i,depth=0):
        if depth>64:raise ValueError('json_depth')
        t=self.text;i=self.ws(i);c=t[i]
        if c=='"':
            m=_STRING.match(t,i)
            if not m:raise ValueError('json_string')
            return m.end()
        if c in '{[':
            closer='}' if c=='{' else ']';i=self.ws(i+1)
            if t[i]==closer:return i+1
            while True:
                if c=='{':
                    if t[i]!='"':raise ValueError('json_key')
                    i=self.ws(self.skip(i,depth+1))
                    if t[i]!=':':raise ValueError('json_colon')
                    i=self.ws(i+1)
                i=self.ws(self.skip(i,depth+1))
                if t[i]==closer:return i+1
                if t[i]!=',':raise ValueError('json_separator')
                i=self.ws(i+1)
        m=_SCALAR.match(t,i)
        if not m:raise ValueError('json_scalar')
        return m.end()
    def fields(self,start=0):
        i=self.ws(start)
        if self.text[i]!='{':raise ValueError('object_required')
        result={};i=self.ws(i+1)
        if self.text[i]=='}':return result
        while True:
            end=self.skip(i);key=json.loads(self.text[i:end])
            if key in result:raise ValueError('duplicate_key')
            i=self.ws(end)+1;i=self.ws(i);end=self.skip(i);result[key]=(i,end);i=self.ws(end)
            if self.text[i]=='}':return result
            i=self.ws(i+1)
    def items(self,span):
        i=self.ws(span[0])
        if self.text[i]!='[':raise ValueError('array_required')
        i=self.ws(i+1)
        if self.text[i]==']':return
        while True:
            end=self.skip(i);yield (i,end);i=self.ws(end)
            if self.text[i]==']':return
            i=self.ws(i+1)
    def read(self,span):return json.loads(self.text[slice(*span)])
    def get(self,fields,key,default=None):return self.read(fields[key]) if key in fields else default


def identifier(v):
    if isinstance(v,bool) or not isinstance(v,(str,int)):raise ValueError('identity_representation')
    s=str(v)
    if not s or s.strip()!=s:raise ValueError('identity_representation')
    return s

def finite_point(v):
    if not isinstance(v,(list,tuple)) or len(v)!=2 or any(isinstance(x,(bool,str)) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in v):raise ValueError('coordinate_invalid')
    return tuple(float(x) for x in v)


def canonical_projection(text):
    v=View(text);f=v.fields()
    expected={'match_id','event_id','carrier_xy','candidate_xy','candidate_ids','defender_xy','target_index','target_outside'}
    if set(f)!=expected:raise ValueError('canonical_schema')
    match=identifier(v.get(f,'match_id'));event=identifier(v.get(f,'event_id'))
    carrier=finite_point(v.get(f,'carrier_xy'))
    ids=tuple(identifier(x) for x in v.get(f,'candidate_ids'))
    xy=tuple(finite_point(x) for x in v.get(f,'candidate_xy'))
    if len(ids)!=len(xy) or not ids or len(set(ids))!=len(ids):raise ValueError('candidate_identity')
    return match,event,carrier,ids,xy


def occurrence_points(row,length):
    match,event,carrier,ids,xy=row
    result=[]
    for role,index,pid,p in [('carrier',None,None,carrier)]+[('candidate',i,pid,p) for i,(pid,p) in enumerate(zip(ids,xy))]:
        if abs(p[0])>length/2:result.append({'match':match,'event':event,'role':role,'candidate_ordinal':index,'player':pid,'xy':p})
    return result


def carrier_reference(event):
    a=event.get('player_id');b=event.get('player_in_possession_id')
    a=identifier(a) if a not in (None,'') else None;b=identifier(b) if b not in (None,'') else None
    if a and b and a!=b:raise ValueError('carrier_reference_conflict')
    if not (a or b):raise ValueError('carrier_reference_missing')
    return a or b


def csv_records(handle):
    """Yield lexical field tokens, not decoded mixed CSV rows."""
    buf=[];quoted=False
    for line in handle:
        buf.append(line);i=0
        while i<len(line):
            if line[i]=='"':
                if quoted and i+1<len(line) and line[i+1]=='"':i+=2;continue
                quoted=not quoted
            i+=1
        if not quoted:
            text=''.join(buf);buf=[];tokens=[];start=0;i=0;q=False
            while i<len(text):
                if text[i]=='"':
                    if q and i+1<len(text) and text[i+1]=='"':i+=2;continue
                    q=not q
                elif text[i]==',' and not q:tokens.append(text[start:i]);start=i+1
                i+=1
            tokens.append(text[start:].rstrip('\r\n'));yield tokens
    if buf or quoted:raise ValueError('csv_unterminated')


def decode_csv(token):
    rows=list(csv.reader(io.StringIO(token),strict=True))
    if token=='':return ''
    if len(rows)!=1 or len(rows[0])!=1:raise ValueError('csv_scalar')
    return rows[0][0]


def exact_events(handle,wanted):
    records=iter(csv_records(handle));header=[decode_csv(t).lstrip('\ufeff') for t in next(records)]
    if len(header)!=len(set(header)):raise ValueError('duplicate_header')
    keep=('event_id','period','time_end','player_id','player_in_possession_id')
    if not set(keep)<=set(header):raise ValueError('event_schema')
    index={k:header.index(k) for k in keep};out={}
    for tokens in records:
        if len(tokens)!=len(header):raise ValueError('csv_width')
        eid=decode_csv(tokens[index['event_id']])
        if eid not in wanted:continue
        if eid in out:raise ValueError('duplicate_matching_event')
        out[eid]={k:decode_csv(tokens[index[k]]) for k in keep}
    if set(out)!=wanted:raise ValueError('event_recovery_missing')
    return out


def metadata_projection(text,wanted):
    v=View(text);f=v.fields();out={}
    for key in ('home_team','away_team'):
        ff=v.fields(f[key][0]);out[key]={'id':identifier(v.get(ff,'id'))}
    if out['home_team']['id']==out['away_team']['id']:raise ValueError('duplicate_team')
    out['home_team_side']=v.get(f,'home_team_side')
    if not isinstance(out['home_team_side'],list) or len(out['home_team_side'])!=2 or any(s not in {'left_to_right','right_to_left'} for s in out['home_team_side']):raise ValueError('direction_unknown')
    for k in ('pitch_length','pitch_width'):
        x=v.get(f,k)
        if isinstance(x,(bool,str)) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0:raise ValueError('dimension_invalid')
        out[k]=float(x)
    players={}
    for span in v.items(f['players']):
        ff=v.fields(span[0]);pid=identifier(v.get(ff,'id'))
        if pid not in wanted:continue
        if pid in players:raise ValueError('duplicate_player')
        team=identifier(v.get(ff,'team_id'))
        if team not in {out['home_team']['id'],out['away_team']['id']}:raise ValueError('player_team')
        pt=v.fields(ff['playing_time'][0]);intervals=[]
        for iv in v.items(pt['by_period']):
            fields=v.fields(iv[0]);intervals.append({k:v.get(fields,k) for k in ('name','start_frame','end_frame')})
        if len({x['name'] for x in intervals})!=len(intervals):raise ValueError('duplicate_period_interval')
        for iv in intervals:
            if iv['name'] not in {'period_1','period_2'}:raise ValueError('interval_structure')
            for k in ('start_frame','end_frame'):
                if iv[k] is not None and type(iv[k]) is not int:raise ValueError('interval_structure')
            if iv['start_frame'] is not None and iv['end_frame'] is not None and iv['start_frame']>iv['end_frame']:raise ValueError('interval_structure')
        players[pid]={'id':pid,'team_id':team,'playing_time':{'by_period':intervals}}
    if set(players)!=wanted:raise ValueError('relevant_roster_missing')
    out['players']=players;return out


def frame_header(text):
    v=View(text);f=v.fields()
    return {k:v.get(f,k) for k in ('frame','period','timestamp')}


def player_samples(text,wanted):
    v=View(text);f=v.fields();result={}
    for span in v.items(f['player_data']):
        ff=v.fields(span[0]);pid=identifier(v.get(ff,'player_id'))
        if pid not in wanted:continue
        if pid in result:raise ValueError('duplicate_tracking_player')
        xy=(v.get(ff,'x'),v.get(ff,'y'))
        # Missing neighboring coordinates remain unavailable rather than repaired.
        if xy[0] is None or xy[1] is None:result[pid]=None;continue
        xy=finite_point(xy);flag=v.get(ff,'is_detected')
        if flag is not None and type(flag) is not bool:raise ValueError('detection_status_invalid')
        result[pid]={'xy':xy,'status':'detected' if flag is True else 'extrapolated' if flag is False else 'unavailable'}
    return result


def neighbors(index,position):
    center=index[position][0]
    return tuple(i for i in range(max(0,position-2),min(len(index),position+3)) if abs(index[i][0]-center)<=200_000)


def verify_point(canonical,native,sign,length):
    if attacking_xy(*native,sign)!=tuple(canonical):raise ValueError('transformation_defect')
    excess=abs(canonical[0])-length/2
    if excess<=0:raise ValueError('dimension_join_defect')
    return excess


def describe(values):
    return {'count':len(values),'minimum':min(values) if values else None,'median':median(values) if values else None,'maximum':max(values) if values else None}


def local_runs(samples,edges):
    """Keys (match,period,player,index); outside sign distinguishes pitch ends."""
    outside=sorted(k for k,v in samples.items() if v is not None and v['side']!=0)
    groups=[]
    for key in outside:
        if groups and key[:3]==groups[-1][-1][:3] and key[3]==groups[-1][-1][3]+1 and samples[key]['side']==samples[groups[-1][-1]]['side']:groups[-1].append(key)
        else:groups.append([key])
    return {'observed_local_runs':len(groups),'censored_runs':sum(any(k in edges for k in group) for group in groups),'single_observed_sample_runs':sum(len(g)==1 for g in groups)}
