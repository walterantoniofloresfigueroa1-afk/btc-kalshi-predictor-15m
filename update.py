import json, urllib.request, datetime, pathlib, math
ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/'data'/'signals.json'
URL='https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=300'
req=urllib.request.Request(URL,headers={'User-Agent':'BTC-15M-simulator/1.0','Accept':'application/json'})
with urllib.request.urlopen(req,timeout=25) as r: raw=json.load(r)
now=int(datetime.datetime.now(datetime.timezone.utc).timestamp())
cs=sorted([{'time':int(x[0]),'low':float(x[1]),'high':float(x[2]),'close':float(x[4])} for x in raw if int(x[0])+300<=now],key=lambda x:x['time'])
if len(cs)<35: raise RuntimeError('Faltan velas cerradas')
cl=[x['close'] for x in cs]
def ema(xs,n):
 k=2/(n+1);v=xs[0]
 for x in xs[1:]:v=x*k+v*(1-k)
 return v
def rsi(xs,n=14):
 d=[xs[i]-xs[i-1] for i in range(1,len(xs))];g=sum(max(v,0) for v in d[:n])/n;l=sum(max(-v,0) for v in d[:n])/n
 for v in d[n:]:g=(g*(n-1)+max(v,0))/n;l=(l*(n-1)+max(-v,0))/n
 return 100 if l==0 else 100-100/(1+g/l)
last=cl[-1];e9=ema(cl,9);e21=ema(cl,21);r=rsi(cl);mom=(last/cl[-4]-1)*100;vol=sum((c['high']-c['low'])/c['close']*100 for c in cs[-14:])/14
ok=.04<=vol<=1.6
signal='UP' if e9>e21 and 52<=r<=68 and mom>.05 and ok else 'DOWN' if e9<e21 and 32<=r<=48 and mom<-.05 and ok else 'ESPERAR'
state={'history':[]}
if PATH.exists():
 try:state=json.loads(PATH.read_text())
 except (ValueError,OSError):pass
history=state.get('history',[])
for entry in history:
 if entry.get('result')!='PENDIENTE':continue
 target=entry['reference_time']+900
 candle=next((c for c in cs if c['time']+300==target),None)
 if candle:
  entry['final_price']=candle['close'];entry['result']='EMPATE' if candle['close']==entry['reference_price'] else ('ACIERTO' if (candle['close']>entry['reference_price'])==(entry['side']=='UP') else 'ERROR')
reference_time=cs[-1]['time']+300
if signal!='ESPERAR' and not any(e['reference_time']==reference_time for e in history):history.append({'reference_time':reference_time,'reference_price':last,'side':signal,'result':'PENDIENTE'})
history=history[-1000:]
state={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'latest':{'signal':signal,'reference_time':reference_time,'price':last,'ema9':round(e9,2),'ema21':round(e21,2),'rsi':round(r,2),'momentum_pct':round(mom,3),'volatility_pct':round(vol,3)},'history':history}
PATH.parent.mkdir(exist_ok=True,parents=True);PATH.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
print('Señal:',signal,'Registros:',len(history))
