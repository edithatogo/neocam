"""Opt-in bounded original-source retrieval. No execution is implied by its presence."""
import argparse,hashlib,json,urllib.request,urllib.parse,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TARGETS={
 'NEP26.pdf':'https://www.ihacpa.gov.au/sites/default/files/2026-03/national_efficient_price_determination_2026-27_2.pdf',
 'NEP26_price_weights.xlsx':'https://www.ihacpa.gov.au/sites/default/files/2026-03/National_Efficient_Price_Determination_2026-27_Price_Weight_Tables.XLSX',
 'NHRA_2026_2031.pdf':'https://federalfinancialrelations.gov.au/sites/federalfinancialrelations.gov.au/files/2026-04/nhra-2026-31-addendum-consolidated.pdf',
 'QH_births_2022.pdf':'https://www.health.qld.gov.au/__data/assets/pdf_file/0020/1378010/8-fac2022x.pdf'}
ALLOWED={'www.ihacpa.gov.au','federalfinancialrelations.gov.au','www.health.qld.gov.au'}
def approved_url(url):
 u=urllib.parse.urlparse(url)
 if u.scheme!='https' or u.hostname not in ALLOWED or u.username or u.password or u.port not in (None,443):
  raise ValueError('Unapproved source or redirect')
 return url

class ApprovedRedirect(urllib.request.HTTPRedirectHandler):
 """Reject an unapproved destination before urllib sends a redirected request."""
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  approved_url(newurl)
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def main():
 p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');a=p.parse_args()
 if not a.fetch:print(json.dumps(TARGETS,indent=2));return
 receipts=[];(ROOT/'original').mkdir(exist_ok=True)
 for name,url in TARGETS.items():
  try:
   approved_url(url)
   opener=urllib.request.build_opener(ApprovedRedirect())
   with opener.open(url,timeout=12) as response:
    approved_url(response.url)
    data=response.read(20_000_001)
   if len(data)>20_000_000:raise ValueError('Oversized response')
   if not data.startswith(b'%PDF-' if name.endswith('.pdf') else b'PK'):raise ValueError('Expected original file signature not HTML')
   target=ROOT/'original'/name;target.write_bytes(data)
   receipts.append({'file':name,'url':url,'status':'saved','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
  except (OSError,ValueError) as e:receipts.append({'file':name,'url':url,'status':'failed','reason':str(e)[:250]})
 (ROOT/'retrieval_receipts.json').write_text(json.dumps(receipts,indent=2))
 print(json.dumps(receipts,indent=2))
if __name__=='__main__':main()
