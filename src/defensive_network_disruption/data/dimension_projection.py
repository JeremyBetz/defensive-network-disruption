"""Selective metadata syntax scanner. Never builds mixed-content records."""
import json
import math
import re

_NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
_STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"')


def project_dimensions(data: bytes) -> dict[str,float]:
    """Retain only root dimension numbers, reject duplicate keys at every level."""
    try:
        text=data.decode('utf-8'); i=0; result={}
        def ws():
            nonlocal i
            while i<len(text) and text[i] in ' \r\n\t': i+=1
        def string(key=False):
            nonlocal i
            m=_STRING.match(text,i)
            if m is None: raise ValueError()
            i=m.end()
            return json.loads(m.group()) if key else None
        def value(depth=0, keep=None):
            nonlocal i
            if depth>64: raise ValueError()
            ws()
            if i>=len(text): raise ValueError()
            c=text[i]
            if keep is not None:
                m=_NUMBER.match(text,i)
                if m is None: raise ValueError()
                v=float(m.group());i=m.end()
                if not math.isfinite(v) or v<=0: raise ValueError()
                result[keep]=v;return
            if c=='{':
                i+=1;ws();seen=set()
                if i<len(text) and text[i]=='}':i+=1;return
                while True:
                    ws();key=string(True)
                    if key in seen:raise ValueError()
                    seen.add(key);ws()
                    if text[i]!=':':raise ValueError()
                    i+=1;value(depth+1,key if depth==0 and key in {'pitch_length','pitch_width'} else None);ws()
                    c=text[i];i+=1
                    if c=='}':break
                    if c!=',':raise ValueError()
            elif c=='[':
                i+=1;ws()
                if text[i]==']':i+=1;return
                while True:
                    value(depth+1);ws();c=text[i];i+=1
                    if c==']':break
                    if c!=',':raise ValueError()
            elif c=='"':string()
            else:
                m=_NUMBER.match(text,i)
                if m:i=m.end()
                else:
                    token=next((t for t in ('true','false','null') if text.startswith(t,i)),None)
                    if token is None:raise ValueError()
                    i+=len(token)
        ws()
        if i>=len(text) or text[i]!='{':raise ValueError()
        value();ws()
        if i!=len(text) or set(result)!={'pitch_length','pitch_width'}:raise ValueError()
        return result
    except (ValueError,IndexError,UnicodeError,RecursionError):
        raise ValueError('metadata_dimension_schema_invalid') from None
