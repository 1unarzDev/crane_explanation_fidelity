"""Real compiled-chain check; no mocked source provenance or model calls."""
import unittest
from pathlib import Path
import prepare_roboboat_fair_inputs_v3 as current

class CurrentBuildProvenanceTests(unittest.TestCase):
    def test_final_mapping_chain_qualifies_all_38_common_robot_sources(self):
        rows=current.common.compiled_source_bindings(current.AUDIT,current.BUILD)
        self.assertEqual(len(rows),38)
        self.assertEqual({r['relative_path'] for r in rows},set(current.common.ROBOT_FILES))
        for row in rows:self.assertTrue(Path(row['original']['path']).is_relative_to(current.common.EXPERIMENTAL_PROJECT))

    def test_intermediate_mapping_chain_is_not_silently_promoted(self):
        intermediate=current.AUDIT.with_name('compiled-source-audit-v4.json')
        with self.assertRaisesRegex(ValueError,'unexpected imported compiler root'):
            current.common.compiled_source_bindings(intermediate,current.BUILD)

if __name__=='__main__':unittest.main()
