from adapter import Adapter
import requests
import json
import urllib
import re

class Entscheidsuche(Adapter):
	name="Entscheidsuche"
	headers={
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:100.0) Gecko/20100101 Firefox/100.0',
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate, br',
		'Referer': 'https://www.zora.uzh.ch/search/?q=test&size=n_10_n',
		'content-type': 'application/json',
		'Origin': 'https://www.zora.uzh.ch',
		'Connection': 'keep-alive',
		'Sec-Fetch-Dest': 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'same-origin'
	}
	host="https://entscheidsuche.pansoft.de"
	suchpfad="/entscheidsuche.v2-*/_search"
	dokumentpfad="/id/eprint/"
	reStrip=re.compile(r"<br>")
	
	def __init__(self):
		super().__init__(self.name)
		
	def request(self, suchstring, filters='', start=0,count=Adapter.LISTSIZE):
		# count is only a recommendation
		# print("Start Entscheidsuche-Request")
		body={"size":count,"_source":{"excludes":["attachment.content"]},"track_total_hits":True,"query":{"bool":{"must":{"query_string":{"query":suchstring,"default_operator":"AND","type":"cross_fields","fields":["title.*^5","abstract.*^3","meta.*^10","attachment.content","reference^3"]}}}},"sort":[{"_score":"desc"},{"id":"desc"}],"from": start}
		if filters:
			body['query']['bool']['filter']=json.loads(filters.replace('@','"'))
		cachekey=suchstring+'#'+filters
		# Wenn der letzte Eintrag davor bekannt ist, "search_after" verwenden.
		if start>0 and cachekey in self.cache:
			treffercache=self.cache[cachekey].trefferliste
			if start-1 in treffercache:
				sort = treffercache[start-1]['sort']
				body['from'] = 0
				body['search_after'] = sort
			
		print(json.dumps(body))
        #"filter":[{"terms":{"attachment.language":["de"]}},{"terms":{"hierarchy":["AG"]}},{"range":{"date":{"lte":1509015759293}}}]}}
        #"filters":"{"language":{"type":"language","payload":["de"]},"hierarchie":{"type":"hierarchie","payload":["CH"]}}"
		response=requests.post(url=self.host+self.suchpfad, headers=self.headers, data=json.dumps(body))
		if response.status_code >= 300:
			return "http-response: "+str(response.status_code)
		rs=json.loads(response.text)
		if not 'hits' in rs:
			return "no valid response"
		treffer=rs['hits']['total']['value']
		trefferliste=[]
		for dokument in rs['hits']['hits']:
			zeile1=self.reStrip.sub(" ",dokument['_source']['title']['de'])
			if 'abstract' in dokument['_source']: zeile2=self.reStrip.sub(" ",dokument['_source']['abstract']['de'])
			else: zeile2=""
			zeile3=""
			sort=dokument['sort']
			url="https://entscheidsuche.ch/view/"+dokument['_id']
			trefferliste.append({'description':[zeile1, zeile2, zeile3],'url': url, 'sort': sort})
		self.addcache(suchstring+'#'+filters,start,treffer,trefferliste)
		# print("Ende Entscheidsuche-Request")		
		return	
