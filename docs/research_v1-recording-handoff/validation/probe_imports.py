"""Read-only guarded import probe; no services, model load, verifier or fitting."""
import importlib.metadata as metadata,json,os,platform,sys,traceback
sys.dont_write_bytecode=True
for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE']:
 os.environ[k]='1'
repo=sys.argv[1];sys.path.insert(0,repo)
def audit(event,args):
 if event in {'socket.connect','socket.getaddrinfo'}:raise RuntimeError('Network blocked by review')
 if event=='open' and args and isinstance(args[0],str) and any(x in args[0].lower() for x in ['final_test','final-test']):raise RuntimeError('Final Test paths blocked by review')
def profile(frame,event,arg):
 if event=='call' and frame.f_code.co_name in {'verify','collect','fit_policy','construct_payoffs','solve_minimax','solve_reliability_first','from_pretrained','evaluate_final_test','evaluate_reserved_final'}:
  raise RuntimeError('Execution blocked by review: '+frame.f_code.co_name)
sys.addaudithook(audit);sys.setprofile(profile)
packages={}
for n in ['httpx','pytest','pydantic','numpy','torch','transformers','sentence-transformers','faiss-cpu']:
 try:packages[n]=metadata.version(n)
 except metadata.PackageNotFoundError:packages[n]=None
print(json.dumps({'interpreter':sys.executable,'version':sys.version,'machine':platform.machine(),'packages':packages}),flush=True)
try:
 from app.game.offline.records import Attempt,Example
 from app.game.offline.collection import RecordingRequest,RecordingBundle
 from app.game.execution_contract import ExecutionContract
except Exception:
 traceback.print_exc();raise SystemExit(1)
print('SCHEMA_IMPORT_PASS; no instances, factories or live methods called')
