#!/usr/bin/env python3
"""Plan reusable gesture sequences; never silently label a cut seamless. Python stdlib + ffmpeg."""
import argparse, json, math, subprocess, tempfile
from pathlib import Path

def read(p): return json.loads(Path(p).read_text())
def write(p,d): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def resolve(catalog,rel): return (Path(catalog).resolve().parent/rel).resolve()
def probe(path):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,r_frame_rate,nb_read_frames','-of','json',str(path)]))['streams'][0]
 n,q=map(int,d['r_frame_rate'].split('/'));return dict(width=d['width'],height=d['height'],fps=n/q,frames=int(d['nb_read_frames']))
def plan(catalog,sequence,duration):
 c=read(catalog); fps=c['fps']; total=math.ceil(duration*fps); clips={x['id']:x for x in c['clips']};cursor=0;out=[];seams=[];i=0
 if not sequence or duration<=0: raise ValueError('Positive duration and nonempty sequence required')
 while cursor<total:
  cid=sequence[i%len(sequence)];x=clips[cid]
  if x['status'] not in ['candidate','approved']:raise ValueError('Clip is unavailable: '+cid)
  start,end=x['usableFrames'];n=min(end-start,total-cursor)
  if n<=0:raise ValueError('Invalid usable frame range: '+cid)
  if out:
   key=out[-1]['clipId']+'>'+cid;edge=c['transitions'].get(key,{})
   # Until a transition is explicitly motion-reviewed, require a cutaway.
   approved=edge.get('status')=='approved' and edge.get('mode')=='direct' and edge.get('reviewEvidence')
   seams.append({'frame':cursor,'seconds':cursor/fps,'from':out[-1]['clipId'],'to':cid,'mode':'direct' if approved else 'cutaway_required','coverFrames':[max(0,cursor-10),min(total,cursor+15)],'reviewEvidence':edge.get('reviewEvidence')})
  out.append({'clipId':cid,'source':str(resolve(catalog,x['source'])),'sourceInFrame':start,'frameCount':n,'timelineInFrame':cursor});cursor+=n;i+=1
 return {'schemaVersion':1,'catalog':str(Path(catalog).resolve()),'fps':fps,'audioDurationSeconds':duration,'frameCount':total,'durationSeconds':total/fps,'segments':out,'seams':seams,'status':'requires_cutaways' if any(s['mode']=='cutaway_required' for s in seams) else 'ready_for_review','note':'Semantic selection must be supplied by the editor. No reverse playback, crossfade, or automatic seamless claim.'}
def render_base(p,out):
 fps=p['fps'];args=['ffmpeg','-v','error','-n'];filters=[];refs=[]
 for i,s in enumerate(p['segments']):
  args+=['-i',s['source']];filters.append(f"[{i}:v]fps={fps},trim=start_frame={s['sourceInFrame']}:end_frame={s['sourceInFrame']+s['frameCount']},setpts=PTS-STARTPTS,setsar=1[v{i}]");refs.append(f'[v{i}]')
 filters.append(''.join(refs)+f"concat=n={len(refs)}:v=1:a=0[v]")
 subprocess.run(args+['-filter_complex',';'.join(filters),'-map','[v]','-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
 actual=probe(out)
 if actual['frames']!=p['frameCount']:raise ValueError('Rendered frame count differs from plan')
def render_review(p,video,audio,covers,out):
 covers=read(covers);required=[s for s in p['seams'] if s['mode']=='cutaway_required'];mapping={x['seamFrame']:x for x in covers['covers']}
 # A missing illustration is not solved with a ghosted face. Leave raw diagnostic base available.
 for s in required:
  if s['frame'] not in mapping or not Path(mapping[s['frame']]['asset']).is_file():raise ValueError('Supply actual cutaway asset for seam frame '+str(s['frame']))
 args=['ffmpeg','-v','error','-n','-i',str(video),'-i',str(audio)];filters=[f"[0:v]fps={p['fps']},tpad=stop_mode=clone:stop_duration=1,trim=end_frame={p['frameCount']},setpts=PTS-STARTPTS[v0]"];info=probe(video)
 for i,s in enumerate(required):
  args+=['-loop','1','-i',mapping[s['frame']]['asset']];a,b=s['coverFrames'];w,h=info['width'],info['height']
  filters.append(f"[{i+2}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x13211e,setsar=1[c{i}]")
  filters.append(f"[v{i}][c{i}]overlay=enable='between(n,{a},{b-1})':shortest=1[v{i+1}]")
 subprocess.run(args+['-filter_complex',';'.join(filters),'-map',f'[v{len(required)}]','-map','1:a:0','-t',str(p['audioDurationSeconds']),'-c:v','libx264','-crf','19','-preset','fast','-c:a','aac','-b:a','192k','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
def main():
 a=argparse.ArgumentParser();s=a.add_subparsers(dest='command',required=True)
 x=s.add_parser('plan');x.add_argument('catalog');x.add_argument('--sequence',nargs='+',required=True);x.add_argument('--duration',type=float,required=True);x.add_argument('--out',required=True)
 x=s.add_parser('render-base');x.add_argument('plan');x.add_argument('--out',required=True)
 x=s.add_parser('render-review');x.add_argument('plan');x.add_argument('--video',required=True);x.add_argument('--audio',required=True);x.add_argument('--covers',required=True);x.add_argument('--out',required=True)
 v=a.parse_args()
 if v.command=='plan':write(v.out,plan(v.catalog,v.sequence,v.duration))
 elif v.command=='render-base':render_base(read(v.plan),v.out)
 else:render_review(read(v.plan),v.video,v.audio,v.covers,v.out)
if __name__=='__main__':main()
