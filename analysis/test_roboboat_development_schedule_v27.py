import copy
import unittest
from roboboat_development_schedule_v27 import schedule

class FreshGeometryTests(unittest.TestCase):
    def population(self):
        rows=[];clusters=[]
        for g in range(8):
            pair=[{'id':f'g{g}-v{v}','cluster_id':f'g{g}','variant':v,'disposition':'DEVELOPMENT_EXPLORATORY'} for v in (1,2)]
            rows+=pair;clusters.append({'cluster_id':f'g{g}','rows':[r['id'] for r in pair]})
        return {'rows':rows,'clusters':clusters}

    def test_inspection_of_one_variant_excludes_entire_geometry(self):
        rows,clusters,lanes,excluded=schedule(self.population(),['g2-v1','g5-v2'])
        self.assertEqual(excluded,['g2','g5']);self.assertEqual(len(clusters),6)
        self.assertFalse({'g2','g5'}&{r['cluster_id'] for r in rows})
        self.assertEqual(len(rows),12);self.assertEqual(len(set(sum(lanes,[]))),12)
        for lane in lanes:
            for i in range(0,len(lane),2):self.assertEqual(lane[i].split('-')[0],lane[i+1].split('-')[0])
        self.assertEqual((rows,clusters,lanes,excluded),schedule(self.population(),['g2-v1','g5-v2']))

    def test_unknown_duplicate_or_incomplete_population_refused(self):
        with self.assertRaises(ValueError):schedule(self.population(),['unknown'])
        p=self.population();p['rows'].append(copy.deepcopy(p['rows'][0]))
        with self.assertRaises(ValueError):schedule(p,[])
        p=self.population();p['clusters'][0]['rows']=p['clusters'][0]['rows'][:1]
        with self.assertRaises(ValueError):schedule(p,[])
        p=self.population();p['rows'][0]['disposition']='CONFIRMATION'
        with self.assertRaises(ValueError):schedule(p,[])

if __name__=='__main__':unittest.main()
