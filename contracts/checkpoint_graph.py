# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from urllib.parse import urlparse
import hashlib,json

def enc(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def ident(v):
 v=v.strip().upper()
 if not 3<=len(v)<=48 or not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in v): raise gl.vm.UserError('invalid id')
 return v
def url(v):
 p=urlparse(v.strip())
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment: raise gl.vm.UserError('clean https required')
 return v.strip()

class MarketSentinel(gl.Contract):
 alerts: TreeMap[str,str]
 def __init__(self): pass
 def key(self,o,i): return str(o).lower()+':'+ident(i)
 @gl.public.write
 def create_alert(self,alert_id:str,asset:str,threshold:str,source_url:str)->None:
  owner=str(gl.message.sender_address).lower(); aid=ident(alert_id); k=self.key(owner,aid)
  if self.alerts.get(k,'') or not asset.strip() or not threshold.strip(): raise gl.vm.UserError('invalid alert')
  self.alerts[k]=enc({'id':aid,'owner':owner,'asset':asset.strip().upper(),'threshold':threshold.strip(),'source':url(source_url),'digest':'','signal':'WAITING','status':'ACTIVE'})
 @gl.public.write
 def sample(self,alert_id:str)->None:
  k=self.key(str(gl.message.sender_address),alert_id);m=json.loads(self.alerts.get(k,'{}'))
  if not m or m['status']!='ACTIVE': raise gl.vm.UserError('inactive alert')
  u=m['source']
  def run():
   body=gl.nondet.web.get(u).body.decode('utf-8')
   if not 20<=len(body)<=60000: raise gl.vm.UserError('source unavailable')
   prompt='Extract whether the asset is above the requested threshold. Return only JSON {"signal":"TRIGGERED"} or {"signal":"CLEAR"}. Asset:'+m['asset']+' Threshold:'+m['threshold']+'\nPAGE:\n'+body
   raw=gl.nondet.exec_prompt(prompt);a=raw.find('{');b=raw.rfind('}')
   signal=json.loads(raw[a:b+1])['signal']
   if signal not in ('TRIGGERED','CLEAR'): raise ValueError('bad signal')
   return enc({'signal':signal,'digest':hashlib.sha256(body.encode()).hexdigest()})
  def valid(r):
   if not isinstance(r,gl.vm.Return): return False
   try: return r.calldata==run()
   except: return False
  out=json.loads(gl.vm.run_nondet_unsafe(run,valid));m.update({'signal':out['signal'],'digest':out['digest']});self.alerts[k]=enc(m)
 @gl.public.write
 def pause(self,alert_id:str)->None:
  k=self.key(str(gl.message.sender_address),alert_id);m=json.loads(self.alerts.get(k,'{}'))
  if not m or m['status']!='ACTIVE': raise gl.vm.UserError('not active')
  m['status']='PAUSED';self.alerts[k]=enc(m)
 @gl.public.view
 def get_alert(self,owner:str,alert_id:str)->str: return self.alerts.get(self.key(owner,alert_id),'{}')
