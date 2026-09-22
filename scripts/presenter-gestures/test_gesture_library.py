import unittest,tempfile,json
from pathlib import Path
import gesture_library as g
class PlanningTests(unittest.TestCase):
 def test_unknown_reverse_and_fractional_tail(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'catalog.json';p.write_text(json.dumps({'fps':25,'clips':[{'id':i,'source':i+'.mp4','status':'candidate','usableFrames':[0,147]} for i in ['a','b']],'transitions':{'a>b':{'status':'approved','mode':'direct','reviewEvidence':'Human review / reference 1'}}}))
   d=g.plan(p,['a','b'],29.507)
   self.assertEqual(d['frameCount'],738)
   self.assertEqual(sum(x['frameCount'] for x in d['segments']),738)
   self.assertEqual(d['seams'][0]['mode'],'direct')
   self.assertEqual(d['seams'][1]['mode'],'cutaway_required')
   self.assertEqual(d['seams'][-1]['coverFrames'][1],738)
 def test_missing_cover_never_publishes_uncovered_cut(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'covers.json';p.write_text('{"covers":[]}');out=Path(t)/'out.mp4'
   with self.assertRaisesRegex(ValueError,'seam frame 25'):
    g.render_review({'seams':[{'mode':'cutaway_required','frame':25}]},'unused.mp4','unused.wav',p,out)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
