import json,subprocess,sys
repos=sys.argv[1:]
Q='''query($o:String!,$n:String!){repository(owner:$o,name:$n){stargazerCount pullRequests(states:MERGED,first:40,orderBy:{field:UPDATED_AT,direction:DESC}){nodes{number title mergedAt changedFiles additions deletions files(first:8){nodes{path}} closingIssuesReferences(first:2){nodes{number bodyText}}}}}}'''
for r in repos:
    o,n=r.split('/')
    p=subprocess.run(['gh','api','graphql','-f','query='+Q,'-f','o='+o,'-f','n='+n],capture_output=True,text=True)
    try: d=json.loads(p.stdout)['data']['repository']
    except Exception: print(r,'ERR'); continue
    for x in d['pullRequests']['nodes']:
        iss=x['closingIssuesReferences']['nodes']
        fs=[f['path'] for f in x['files']['nodes']]
        t=[f for f in fs if 'test' in f.lower() or 'spec' in f.lower()]
        s=[f for f in fs if f not in t and not f.endswith(('.md','.json','.yml','.lock'))]
        if iss and t and s and x['changedFiles']<=5 and x['additions']+x['deletions']<=80 and len(iss[0]['bodyText'])>150:
            print(r,d['stargazerCount'],x['number'],x['title'][:60],x['mergedAt'][:10],'issue',iss[0]['number'],len(iss[0]['bodyText']),s,t)
